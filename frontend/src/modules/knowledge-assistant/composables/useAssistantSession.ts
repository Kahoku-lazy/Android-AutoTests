/**
 * 知识库助手会话编排：语音（麦克风 + 播放器）与文字（DeepSeek Flash）两种方式。
 *
 * 组件只调用 start / stop / interrupt / submitText；本 composable 负责浏览器资源的
 * 建立与释放，并把服务端事件转成页面状态。语音与文字不共享上下文。
 */
import { computed, ref } from "vue"
import { getToken } from "@/shared/auth/token-storage"
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

  const isActive = computed(() => ACTIVE_STATES.includes(state.value))
  const canInterrupt = computed(() => state.value === "speaking" || state.value === "thinking")
  const canType = computed(() => canSendText(mode.value, socketOpen.value, state.value))

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

    const token = getToken()
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
   * Args:
   *   text: 用户输入；空白内容不发送。
   */
  function submitText(text: string): void {
    const value = text.trim()
    if (!canType.value || !value) return
    noticeMessage.value = ""
    sendControl({ type: "text", text: value })
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
    socket.onclose = () => {
      if (!closing && state.value !== "error") fail(KB_SOCKET_ERROR)
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
