/**
 * 语音会话编排：麦克风、WebSocket、播放器与消息列表。
 *
 * 组件只调用 start / stop / interrupt；本 composable 负责浏览器资源
 * 的建立与释放，并把服务端事件转成页面状态。
 */
import { computed, ref } from "vue"
import { getToken } from "@/shared/auth/token-storage"
import { AudioPlayer } from "../audio/audioPlayer"
import { MicCapture, listMicrophoneDevices, type MicrophoneDevice } from "../audio/micCapture"
import {
  KB_INPUT_SAMPLE_RATE,
  KB_MIC_ERROR,
  KB_OUTPUT_SAMPLE_RATE,
  KB_SOCKET_ERROR,
  KB_UNAUTHORIZED_ERROR,
  KB_WS_PATH,
} from "../constants"
import { applyServerEvent } from "../helpers/transcript"
import type { ServerEvent, SessionInfo, TranscriptMessage, VoiceState } from "../types"

const ACTIVE_STATES: VoiceState[] = ["connecting", "listening", "thinking", "speaking"]

/**
 * 知识库助手语音会话。
 *
 * Returns:
 *   messages / state / errorMessage / session / isActive / canInterrupt，
 *   以及 start / stop / interrupt / dispose 四个动作。
 */
export function useVoiceSession() {
  const messages = ref<TranscriptMessage[]>([])
  const state = ref<VoiceState>("idle")
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
  let readyResolve: (() => void) | null = null
  let readyReject: ((reason?: unknown) => void) | null = null

  const isActive = computed(() => ACTIVE_STATES.includes(state.value))
  const canInterrupt = computed(() => state.value === "speaking" || state.value === "thinking")

  async function loadDevices(): Promise<void> {
    devices.value = await listMicrophoneDevices()
  }

  function settleReady(error?: Error): void {
    if (error) readyReject?.(error)
    else readyResolve?.()
    readyResolve = null
    readyReject = null
  }

  function waitReady(): Promise<void> {
    if (session.value) return Promise.resolve()
    return new Promise((resolve, reject) => {
      readyResolve = resolve
      readyReject = reject
    })
  }

  async function start(mode = "omni", withMic = true): Promise<void> {
    if (isActive.value) return
    errorMessage.value = ""
    noticeMessage.value = ""
    session.value = null
    messages.value = []
    state.value = "connecting"
    micLevel.value = 0
    sentFrames.value = 0
    closing = false

    const token = getToken()
    if (!token) {
      fail(KB_UNAUTHORIZED_ERROR)
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
      if (withMic) {
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
      } else {
        mic = null
      }
      openSocket(token, mode)
      if (!withMic) await waitReady()
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

  async function sendText(text: string, mode = "pipeline"): Promise<void> {
    const value = text.trim()
    if (!value) return
    try {
      if (!isActive.value) {
        await start(mode, false)
      } else if (!session.value) {
        await waitReady()
      }
      if (state.value === "error") return
      sendControl({ type: "text", text: value })
    } catch {
      // fail() 已把可读错误写到页面；这里不重复抛给组件
    }
  }

  function stop(): void {
    settleReady(new Error("会话已结束"))
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

  function dispose(): void {
    settleReady(new Error("会话已释放"))
    cleanup()
    state.value = "idle"
  }

  function openSocket(token: string, mode: string): void {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const params = new URLSearchParams({ token, mode })
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
          translationLanguage: event.translation_language,
          logPath: event.log_path,
        }
        state.value = "listening"
        settleReady()
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
    settleReady(new Error(message))
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
    sendText,
    stop,
    interrupt,
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
