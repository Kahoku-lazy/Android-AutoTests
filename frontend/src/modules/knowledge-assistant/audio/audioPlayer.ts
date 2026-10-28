/**
 * 助手音频播放：把下行 PCM16 排程到 AudioBufferSourceNode。
 *
 * 24kHz 的 AudioBuffer 交给浏览器重采样到设备采样率；播放进度按
 * 已排程片段的实际播放时间累计，回传给服务端用于打断截断。
 */
import { KB_OUTPUT_SAMPLE_RATE, KB_PLAYOUT_REPORT_MS } from "../constants"
import { pcm16ToFloat32 } from "./pcm"

interface PlaybackRecord {
  source: AudioBufferSourceNode
  itemId: string
  startAt: number
  duration: number
}

export interface AudioPlayerOptions {
  sampleRate?: number
  onPlayed?: (itemId: string, playedMs: number) => void
}

/**
 * 助手音频播放器。
 *
 * Attributes:
 *   sampleRate: 下行 PCM 的采样率（模型输出采样率）。
 */
export class AudioPlayer {
  private context: AudioContext | null = null
  private sampleRate = KB_OUTPUT_SAMPLE_RATE
  private nextStart = 0
  private currentItemId = ""
  private records: PlaybackRecord[] = []
  private timer: number | null = null
  private onPlayed: ((itemId: string, playedMs: number) => void) | null = null

  /**
   * 创建播放上下文并开始周期回报播放进度。
   *
   * Args:
   *   options: 输出采样率与播放进度回调。
   *
   * Raises:
   *   Error: 浏览器不支持 AudioContext 或被自动播放策略阻止。
   */
  async start(options: AudioPlayerOptions = {}): Promise<void> {
    this.sampleRate = options.sampleRate ?? KB_OUTPUT_SAMPLE_RATE
    this.onPlayed = options.onPlayed ?? null
    const AudioContextCtor =
      window.AudioContext ??
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    if (!AudioContextCtor) throw new Error("浏览器不支持 AudioContext")
    this.context = new AudioContextCtor()
    await this.context.resume()
    this.nextStart = this.context.currentTime
    this.timer = window.setInterval(() => this.report(), KB_PLAYOUT_REPORT_MS)
  }

  /**
   * 更新输出采样率；变化时清空已排程音频。
   *
   * Args:
   *   rate: 模型输出采样率。
   */
  setSampleRate(rate: number): void {
    if (rate <= 0 || rate === this.sampleRate) return
    this.clear()
    this.sampleRate = rate
  }

  /**
   * 标记当前播放条目；服务端在音频前发 audio_item 时调用。
   *
   * Args:
   *   itemId: 助手条目 id。
   */
  setItem(itemId: string): void {
    if (itemId) this.currentItemId = itemId
  }

  /**
   * 把一帧下行 PCM16 排到播放队列末尾。
   *
   * Args:
   *   buffer: WebSocket 二进制音频。
   */
  enqueue(buffer: ArrayBuffer): void {
    if (!this.context) return
    const samples = pcm16ToFloat32(buffer)
    if (samples.length === 0) return

    const audioBuffer = this.context.createBuffer(1, samples.length, this.sampleRate)
    audioBuffer.copyToChannel(samples, 0)
    const source = this.context.createBufferSource()
    source.buffer = audioBuffer
    source.connect(this.context.destination)

    const startAt = Math.max(this.context.currentTime + 0.01, this.nextStart)
    source.start(startAt)
    const duration = samples.length / this.sampleRate
    this.nextStart = startAt + duration
    this.records.push({
      source,
      itemId: this.currentItemId,
      startAt,
      duration,
    })
  }

  /**
   * 清空播放队列并停止所有已排程片段（用于打断）。
   */
  clear(): void {
    for (const record of this.records) {
      try {
        record.source.stop()
      } catch {
        // 片段可能已经自然播完；停止失败时无需处理
      }
    }
    this.records = []
    if (this.context) this.nextStart = this.context.currentTime
  }

  /**
   * 停止播放并释放 AudioContext。
   */
  stop(): void {
    this.clear()
    this.onPlayed = null
    if (this.timer !== null) {
      window.clearInterval(this.timer)
      this.timer = null
    }
    if (this.context) {
      void this.context.close()
      this.context = null
    }
  }

  /**
   * 计算某个条目实际播放到的毫秒数。
   *
   * Args:
   *   itemId: 助手条目 id。
   *
   * Returns:
   *   已播放毫秒数；上下文不存在时为 0。
   */
  playedMs(itemId: string): number {
    if (!this.context) return 0
    const now = this.context.currentTime
    const seconds = this.records
      .filter((record) => record.itemId === itemId && now > record.startAt)
      .reduce((total, record) => total + Math.min(now - record.startAt, record.duration), 0)
    return Math.floor(seconds * 1000)
  }

  private report(): void {
    if (!this.currentItemId || !this.onPlayed) return
    this.onPlayed(this.currentItemId, this.playedMs(this.currentItemId))
  }
}
