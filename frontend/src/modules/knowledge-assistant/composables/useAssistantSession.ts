/**
 * 知识库助手会话编排：语音（麦克风 + 播放器）与文字（DeepSeek Flash）两种方式。
 *
 * 组件只调用 start / stop / interrupt / submitText；本 composable 负责浏览器资源的
 * 建立与释放，并把服务端事件转成页面状态。语音与文字不共享上下文。
 */
import { computed, ref } from "vue"
import { ensureFreshToken, refreshAccessToken } from "@/shared/auth/token-refresh"
import { AudioPlayer } from "../audio/audioPlayer"
import { MicCapture, listMicrophoneDevices, type MicrophoneDevice } from "../audio/micCapture"
import {
  KB_INPUT_SAMPLE_RATE,
  KB_MIC_ERROR,
  KB_MODE_TEXT,
  KB_MODE_VOICE,
  KB_OUTPUT_SAMPLE_RATE,
  KB_SOCKET_ERROR,
  KB_UNAUTHORIZED_ERROR,
  KB_WS_PATH,
} from "../constants"
import { canSendText } from "../helpers/mode"
import { applyServerEvent } from "../helpers/transcript"
import type {
  AssistantMode,
  ServerEvent,
  SessionInfo,
  TranscriptMessage,
  VoiceState,
} from "../types"

const ACTIVE_STATES: VoiceState[] = ["connecting", "listening", "thinking", "speaking"]

/**
 * 知识库助手会话（语音 / 文字）。
 *
 * Returns:
 *   messages / state / mode / canType / session / canInterrupt，
 *   以及 start / stop / interrupt / submitText / dispose 五个动作。
 */
export function useAssistantSession() {
  const messages = ref<TranscriptMessage[]>([])
  const state = ref<VoiceState>("idle")
  const mode = ref<AssistantMode>(KB_MODE_VOICE)
  const socketOpen = ref(false)
  const errorMessage = ref("")
  const noticeMessage = ref("")
  const session = ref<SessionInfo | null>(null)
  const inputRate = ref(KB_INPUT_SAMPLE_RATE)
  const micLevel = ref(0)
  const sentFrames = ref(0)
  const devices = ref<MicrophoneDevice[]>([])
  const selectedDeviceId = ref("")

  let socket: WebSocket | null = null
  let mic: MicCapture | null = null
  let player: AudioPlayer | null = null
  let closing = false
  /** 建连阶段收到的错误帧：等 close 决定是重连还是失败，避免把可恢复的错误落成错误态 */
  let pendingError = ""
  /** 本次会话是否已为 4401 补偿过一次：一次会话最多重连一次 */
  let authRetried = false
  /** 连接就绪前用户发出的文本：按顺序排队，ready 后一次补发，避免「先等连接再让用户重打」 */
  let pendingTexts: string[] = []

  const isActive = computed(() => ACTIVE_STATES.includes(state.value))
  const canInterrupt = computed(() => state.value === "speaking" || state.value === "thinking")
  const canType = computed(() => canSendText(mode.value, state.value))

  async function loadDevices(): Promise<void> {
    devices.value = await listMicrophoneDevices()
  }

  async function start(nextMode: AssistantMode = KB_MODE_VOICE): Promise<void> {
    if (isActive.value) return
    mode.value = nextMode
    errorMessage.value = ""
    noticeMessage.value = ""
    session.value = null
    messages.value = []
    state.value = "connecting"
    micLevel.value = 0
    sentFrames.value = 0
    socketOpen.value = false
    closing = false
    pendingError = ""
    authRetried = false

    // 建连前确保凭证有效：access 只有 1 小时寿命，过期后 WebSocket 没有 401 兜底
    let token: string
    try {
      token = await ensureFreshToken()
    } catch {
      token = ""
    }
    if (!token) {
      fail(KB_UNAUTHORIZED_ERROR)
      return
    }

    // 文字方式不碰麦克风与播放器：没有浏览器音频权限要求。
    if (nextMode === KB_MODE_TEXT) {
      openSocket(token, nextMode)
      return
    }

    try {
      // 播放器先建立 AudioContext（点击手势内），再接麦克风，避免播放上下文被自动播放策略挂起。
      player = new AudioPlayer()
      await player.start({
        sampleRate: KB_OUTPUT_SAMPLE_RATE,
        onPlayed: (itemId, playedMs) => {
          sendControl({ type: "played", item_id: itemId, played_ms: playedMs })
        },
      })
      mic = new MicCapture()
      await mic.start({
        targetRate: inputRate.value,
        deviceId: selectedDeviceId.value || undefined,
        onFrame: (pcm) => sendAudio(pcm),
        onLevel: (level) => {
          micLevel.value = level
        },
      })
      void loadDevices()
      openSocket(token, nextMode)
    } catch (error) {
      const message =
        error instanceof DOMException && error.name === "NotAllowedError"
          ? KB_MIC_ERROR
          : error instanceof Error
            ? error.message
            : KB_SOCKET_ERROR
      fail(message)
    }
  }

  function stop(): void {
    settleStreaming("interrupted")
    cleanup()
    state.value = "idle"
    errorMessage.value = ""
    noticeMessage.value = ""
    micLevel.value = 0
  }

  function interrupt(): void {
    if (!isActive.value) return
    sendControl({ type: "interrupt" })
    player?.clear()
    state.value = "listening"
  }

  /**
   * 发送一条文字提问。
   *
   * 文字方式不需要先点「开始对话」：未连接时先记下这句话并自动建连，
   * 连接就绪（收到 `ready`）后由 `flushPendingText()` 补发。
   *
   * Args:
   *   text: 用户输入；空白内容不发送。
   */
  function submitText(text: string): void {
    const value = text.trim()
    if (!canType.value || !value) return
    noticeMessage.value = ""
    if (socketOpen.value) {
      sendControl({ type: "text", text: value })
      return
    }
    pendingTexts.push(value)
    void start(KB_MODE_TEXT)
  }

  /** 把连接就绪前排队的文本按顺序补发（每条只发一次） */
  function flushPendingTexts(): void {
    if (!pendingTexts.length) return
    const batch = pendingTexts
    pendingTexts = []
    for (const item of batch) sendControl({ type: "text", text: item })
  }

  function dispose(): void {
    cleanup()
    state.value = "idle"
  }

  function openSocket(token: string, nextMode: AssistantMode): void {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const params = new URLSearchParams({ token, mode: nextMode })
    const url = `${protocol}//${window.location.host}${KB_WS_PATH}?${params}`
    socket = new WebSocket(url)
    socket.binaryType = "arraybuffer"
    socket.onmessage = (event: MessageEvent) => handleMessage(event)
    socket.onerror = () => {
      if (!closing) fail(KB_SOCKET_ERROR)
    }
    socket.onclose = (event: CloseEvent) => {
      socket = null
      socketOpen.value = false
      if (closing) return
      // 4401 = 服务端鉴权拒绝：多为 access 过期，换新凭证重连一次
      if (event.code === 4401 && !authRetried) {
        authRetried = true
        void reconnectWithFreshToken()
        return
      }
      if (state.value === "error") return
      fail(pendingError || KB_SOCKET_ERROR)
    }
  }

  /**
   * 4401 之后换新凭证重连一次。
   *
   * 续期失败才把「登录已过期」呈现给用户；重连仍被拒会走 `onclose` 的通用失败分支，
   * 因为 `authRetried` 已置真，不会再循环。
   */
  async function reconnectWithFreshToken(): Promise<void> {
    if (!isActive.value) return
    try {
      const token = await refreshAccessToken()
      pendingError = ""
      state.value = "connecting"
      openSocket(token, mode.value)
    } catch {
      fail(KB_UNAUTHORIZED_ERROR)
    }
  }

  function handleMessage(event: MessageEvent): void {
    if (typeof event.data === "string") {
      const payload = parseEvent(event.data)
      if (payload) handleServerEvent(payload)
      return
    }
    if (event.data instanceof ArrayBuffer) {
      player?.enqueue(event.data)
    }
  }

  function handleServerEvent(event: ServerEvent): void {
    switch (event.type) {
      case "ready":
        inputRate.value = event.input_sample_rate || KB_INPUT_SAMPLE_RATE
        mic?.setTargetRate(inputRate.value)
        player?.setSampleRate(event.output_sample_rate || KB_OUTPUT_SAMPLE_RATE)
        session.value = {
          agentName: event.agent_name,
          model: event.model,
          voice: event.voice,
          mode: event.mode,
          logPath: event.log_path,
        }
        socketOpen.value = true
        state.value = "listening"
        // 用户在建连前就发出了问题：连接就绪后按顺序补发
        flushPendingTexts()
        break
      case "audio_item":
        player?.setItem(event.item_id)
        break
      case "clear_audio":
        player?.clear()
        break
      case "state":
        state.value = normalizeState(event.value)
        break
      case "error":
        // 建连阶段的错误多为鉴权拒绝：先记下，交给 onclose 决定「重连」还是「失败」
        if (state.value === "connecting") {
          pendingError = event.message || ""
          break
        }
        fail(event.message || KB_SOCKET_ERROR)
        break
      case "notice":
        noticeMessage.value = event.message
        break
      case "closed":
        settleStreaming("done")
        cleanup()
        state.value = "idle"
        break
      default:
        messages.value = applyServerEvent(messages.value, event)
    }
  }

  function sendAudio(pcm: Int16Array): void {
    if (!socket || socket.readyState !== WebSocket.OPEN) return
    if (sentFrames.value === 0) noticeMessage.value = ""
    sentFrames.value += 1
    socket.send(pcm)
  }

  function sendControl(payload: Record<string, unknown>): void {
    if (!socket || socket.readyState !== WebSocket.OPEN) return
    socket.send(JSON.stringify(payload))
  }

  function fail(message: string): void {
    if (state.value === "error") return
    settleStreaming("error")
    errorMessage.value = message
    state.value = "error"
    micLevel.value = 0
    cleanup()
  }

  function settleStreaming(status: "done" | "interrupted" | "error"): void {
    messages.value = messages.value
      .filter((message) => message.text.trim().length > 0)
      .map((message) =>
        message.status !== "streaming"
          ? message
          : {
              ...message,
              status: message.role === "user" && status === "interrupted" ? "done" : status,
            },
      )
  }

  function cleanup(): void {
    closing = true
    socketOpen.value = false
    // 会话结束就丢弃未发出的文本，避免下一次会话把上一句发出去
    pendingTexts = []
    if (socket) {
      socket.onmessage = null
      socket.onerror = null
      socket.onclose = null
      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
        socket.close(1000)
      }
      socket = null
    }
    mic?.stop()
    mic = null
    player?.stop()
    player = null
    session.value = null
  }

  return {
    messages,
    state,
    mode,
    socketOpen,
    canType,
    errorMessage,
    noticeMessage,
    session,
    micLevel,
    sentFrames,
    devices,
    selectedDeviceId,
    loadDevices,
    isActive,
    canInterrupt,
    start,
    stop,
    interrupt,
    submitText,
    dispose,
  }
}

function parseEvent(raw: string): ServerEvent | null {
  try {
    const parsed = JSON.parse(raw) as { type?: unknown }
    if (!parsed || typeof parsed !== "object" || typeof parsed.type !== "string") {
      return null
    }
    return parsed as ServerEvent
  } catch {
    // 非 JSON 文本帧不是本通道的合法消息：忽略，不打断会话
    return null
  }
}

function normalizeState(value: string): VoiceState {
  if (value === "listening" || value === "thinking" || value === "speaking") {
    return value
  }
  if (value === "error") return "error"
  if (value === "idle") return "idle"
  return "listening"
}
