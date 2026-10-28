/**
 * 麦克风采集：AudioWorklet 为主、ScriptProcessor 兜底。
 *
 * 只负责把麦克风样本按固定时长切块、重采样到模型输入采样率，
 * 并通过 onFrame 交给 WebSocket；不处理连接与 UI 状态。
 */
import { KB_CAPTURE_CHUNK_MS, KB_INPUT_SAMPLE_RATE } from "../constants"
import { toInputPcm16 } from "./pcm"

const WORKLET_NAME = "kb-capture"

const WORKLET_CODE = `
class KbCaptureProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const channels = inputs[0]
    if (!channels || channels.length === 0) return true
    // 选能量最大的声道，而不是直接平均：立体声麦克风常见“只有一侧有声音”
    // 或两声道反相，平均会把语音抵消成静音/噪声。
    let best = channels[0]
    let bestEnergy = -1
    for (let channel = 0; channel < channels.length; channel += 1) {
      const data = channels[channel]
      let energy = 0
      for (let index = 0; index < data.length; index += 1) {
        energy += data[index] * data[index]
      }
      if (energy > bestEnergy) {
        bestEnergy = energy
        best = data
      }
    }
    this.port.postMessage(best.slice(0))
    return true
  }
}
registerProcessor("${WORKLET_NAME}", KbCaptureProcessor)
`

export interface MicrophoneDevice {
  deviceId: string
  label: string
}

export interface MicCaptureOptions {
  targetRate?: number
  chunkMs?: number
  deviceId?: string
  onFrame: (pcm: Int16Array) => void
  onLevel?: (level: number) => void
}

/**
 * 枚举当前浏览器可见的麦克风；未授权时 label 可能为空。
 *
 * Returns:
 *   `{deviceId, label}` 列表；枚举失败时返回空数组。
 */
export async function listMicrophoneDevices(): Promise<MicrophoneDevice[]> {
  if (!navigator.mediaDevices?.enumerateDevices) return []
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    return devices
      .filter((device) => device.kind === "audioinput")
      .map((device, index) => ({
        deviceId: device.deviceId,
        label: device.label || `麦克风 ${index + 1}`,
      }))
  } catch {
    // 权限未授予或浏览器不支持枚举：页面回退到“系统默认”
    return []
  }
}

function rmsLevel(samples: Float32Array): number {
  let sum = 0
  for (let index = 0; index < samples.length; index += 1) {
    sum += samples[index] * samples[index]
  }
  return Math.sqrt(sum / Math.max(1, samples.length))
}

/**
 * 麦克风采集器。
 *
 * Attributes:
 *   targetRate: 目标采样率（模型输入）。
 *   chunkMs: 每块时长（毫秒）。
 */
export class MicCapture {
  private context: AudioContext | null = null
  private stream: MediaStream | null = null
  private source: MediaStreamAudioSourceNode | null = null
  private worklet: AudioWorkletNode | null = null
  private processor: ScriptProcessorNode | null = null
  private workletUrl: string | null = null
  private pending: Float32Array[] = []
  private pendingSamples = 0
  private targetRate = KB_INPUT_SAMPLE_RATE
  private chunkMs = KB_CAPTURE_CHUNK_MS
  private onFrame: ((pcm: Int16Array) => void) | null = null
  private onLevel: ((level: number) => void) | null = null
  private receivedSamples = 0
  private fallbackTimer: number | null = null
  private dcPrevInput = 0
  private dcPrevOutput = 0

  /**
   * 打开麦克风并开始采集。
   *
   * Args:
   *   options: 目标采样率、分块时长与帧回调。
   *
   * Raises:
   *   Error: 浏览器不支持或用户拒绝麦克风权限。
   */
  async start(options: MicCaptureOptions): Promise<void> {
    this.targetRate = options.targetRate ?? KB_INPUT_SAMPLE_RATE
    this.chunkMs = options.chunkMs ?? KB_CAPTURE_CHUNK_MS
    this.onFrame = options.onFrame
    this.onLevel = options.onLevel ?? null
    this.receivedSamples = 0
    this.dcPrevInput = 0
    this.dcPrevOutput = 0
    this.clearFallbackTimer()

    const AudioContextCtor =
      window.AudioContext ??
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    if (!AudioContextCtor) throw new Error("浏览器不支持 AudioContext")

    // 先在点击手势内创建并恢复 AudioContext，再 await 麦克风授权：
    // 反过来先等授权，部分浏览器会把 context 留在 suspended，采集一帧都不会出。
    // 优先让浏览器原生重采样到模型输入采样率；不支持指定采样率时回退默认上下文。
    let context: AudioContext
    try {
      context = new AudioContextCtor({ sampleRate: this.targetRate })
    } catch {
      context = new AudioContextCtor()
    }
    this.context = context

    try {
      await context.resume()
      const audioConstraints: MediaTrackConstraints = {
        // 与 realtime_voice_demo 的原始 sounddevice 输入保持一致：
        // 不用浏览器的 AEC/降噪/AGC，避免真实语音被压坏导致服务端 VAD 不触发。
        channelCount: { ideal: 2 },
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false,
      }
      if (options.deviceId) {
        audioConstraints.deviceId = { exact: options.deviceId }
      }
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: audioConstraints,
      })
      this.source = context.createMediaStreamSource(this.stream)

      if (context.audioWorklet && typeof AudioWorkletNode !== "undefined") {
        const blob = new Blob([WORKLET_CODE], { type: "application/javascript" })
        this.workletUrl = URL.createObjectURL(blob)
        await context.audioWorklet.addModule(this.workletUrl)
        const node = new AudioWorkletNode(context, WORKLET_NAME)
        node.port.onmessage = (event: MessageEvent<Float32Array>) => {
          this.pushSamples(event.data)
        }
        this.worklet = node
        this.source.connect(node)
        node.connect(context.destination)
        // 授权弹窗期间 context 可能被再次挂起：连接好节点后再恢复一次。
        await context.resume()
        this.armWorkletFallback()
      } else {
        this.startScriptProcessor()
        await context.resume()
      }
    } catch (error) {
      this.stop()
      throw error
    }
  }

  /**
   * 更新目标采样率；已采集但未发送的样本按新采样率转换。
   *
   * Args:
   *   rate: 模型输入采样率。
   */
  setTargetRate(rate: number): void {
    if (rate > 0) this.targetRate = rate
  }

  /**
   * 停止采集并释放麦克风、AudioContext 与 Worklet URL。
   */
  stop(): void {
    this.onFrame = null
    this.onLevel = null
    this.clearFallbackTimer()
    if (this.worklet) {
      this.worklet.port.onmessage = null
      this.worklet.disconnect()
      this.worklet = null
    }
    if (this.processor) {
      this.processor.onaudioprocess = null
      this.processor.disconnect()
      this.processor = null
    }
    if (this.source) {
      this.source.disconnect()
      this.source = null
    }
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop())
      this.stream = null
    }
    if (this.workletUrl) {
      URL.revokeObjectURL(this.workletUrl)
      this.workletUrl = null
    }
    if (this.context) {
      void this.context.close()
      this.context = null
    }
    this.pending = []
    this.pendingSamples = 0
  }

  private armWorkletFallback(): void {
    // AudioWorklet 在少数浏览器/设备上会“已连接但不回调”：1.5 秒内没有样本就切 ScriptProcessor。
    this.clearFallbackTimer()
    this.fallbackTimer = window.setTimeout(() => {
      if (this.receivedSamples === 0) this.startScriptProcessor()
    }, 1500)
  }

  private clearFallbackTimer(): void {
    if (this.fallbackTimer === null) return
    window.clearTimeout(this.fallbackTimer)
    this.fallbackTimer = null
  }

  private startScriptProcessor(): void {
    if (!this.context || !this.source) return
    this.clearFallbackTimer()
    if (this.worklet) {
      this.worklet.port.onmessage = null
      this.worklet.disconnect()
      this.worklet = null
    }
    if (this.workletUrl) {
      URL.revokeObjectURL(this.workletUrl)
      this.workletUrl = null
    }
    if (this.processor) return
    this.source.disconnect()
    const node = this.context.createScriptProcessor(4096, 1, 1)
    node.onaudioprocess = (event) => {
      this.pushSamples(this.monoBuffer(event.inputBuffer))
    }
    this.processor = node
    this.source.connect(node)
    node.connect(this.context.destination)
    void this.context.resume()
  }

  private monoBuffer(buffer: AudioBuffer): Float32Array {
    let best = buffer.getChannelData(0)
    let bestEnergy = -1
    for (let channel = 0; channel < buffer.numberOfChannels; channel += 1) {
      const data = buffer.getChannelData(channel)
      let energy = 0
      for (let index = 0; index < data.length; index += 1) {
        energy += data[index] * data[index]
      }
      if (energy > bestEnergy) {
        bestEnergy = energy
        best = data
      }
    }
    return new Float32Array(best)
  }

  private removeDc(samples: Float32Array): Float32Array {
    // 一阶高通，去掉麦克风 DC 偏置/低频嗡声；不该让这些能量被当成“有信号”。
    const output = new Float32Array(samples.length)
    let previousInput = this.dcPrevInput
    let previousOutput = this.dcPrevOutput
    for (let index = 0; index < samples.length; index += 1) {
      const input = samples[index]
      const value = input - previousInput + 0.99 * previousOutput
      output[index] = value
      previousInput = input
      previousOutput = value
    }
    this.dcPrevInput = previousInput
    this.dcPrevOutput = previousOutput
    return output
  }

  private pushSamples(samples: Float32Array): void {
    if (!this.onFrame || !this.context || samples.length === 0) return
    this.receivedSamples += samples.length
    if (this.receivedSamples > 0) this.clearFallbackTimer()
    const filtered = this.removeDc(samples)
    this.pending.push(filtered)
    this.pendingSamples += filtered.length

    const chunkSamples = Math.max(1, Math.round((this.context.sampleRate * this.chunkMs) / 1000))
    while (this.pendingSamples >= chunkSamples) {
      const chunk = this.takeSamples(chunkSamples)
      this.pendingSamples -= chunkSamples
      this.onLevel?.(rmsLevel(chunk))
      const pcm = toInputPcm16(chunk, this.context.sampleRate, this.targetRate)
      if (pcm.length > 0) this.onFrame(pcm)
    }
  }

  private takeSamples(count: number): Float32Array {
    const output = new Float32Array(count)
    let offset = 0
    while (offset < count && this.pending.length > 0) {
      const head = this.pending[0]
      const needed = count - offset
      if (head.length <= needed) {
        output.set(head, offset)
        offset += head.length
        this.pending.shift()
      } else {
        output.set(head.subarray(0, needed), offset)
        this.pending[0] = head.subarray(needed)
        offset += needed
      }
    }
    return output
  }
}
