/**
 * PCM 与重采样纯函数：浏览器 Float32 音频 <-> 服务端 PCM16。
 *
 * 只做数值转换；不碰 AudioContext / WebSocket，便于 jsdom 单测。
 */
import { KB_INPUT_SAMPLE_RATE } from "../constants"

const PCM16_MAX = 32767
const PCM16_MIN = -32768

/**
 * 把浮点样本夹到 Int16 范围并取整。
 *
 * Args:
 *   value: 浮点样本，通常来自 AudioWorklet（[-1, 1]）。
 *
 * Returns:
 *   Int16 整数。
 */
export function clamp16(value: number): number {
  if (!Number.isFinite(value)) return 0
  if (value >= PCM16_MAX) return PCM16_MAX
  if (value <= PCM16_MIN) return PCM16_MIN
  return Math.round(value)
}

/**
 * Float32 [-1, 1] -> 小端 Int16 PCM。
 *
 * Args:
 *   samples: 单声道浮点样本。
 *
 * Returns:
 *   Int16 样本。
 */
export function float32ToPcm16(samples: Float32Array): Int16Array {
  const output = new Int16Array(samples.length)
  for (let index = 0; index < samples.length; index += 1) {
    output[index] = clamp16(samples[index] * PCM16_MAX)
  }
  return output
}

/**
 * 小端 Int16 PCM -> Float32 [-1, 1]。
 *
 * Args:
 *   buffer: WebSocket 收到的二进制音频；奇数尾字节会被忽略。
 *
 * Returns:
 *   单声道浮点样本。
 */
export function pcm16ToFloat32(buffer: ArrayBuffer): Float32Array {
  const usableBytes = buffer.byteLength - (buffer.byteLength % 2)
  const view = new DataView(buffer, 0, usableBytes)
  const output = new Float32Array(usableBytes / 2)
  for (let index = 0; index < output.length; index += 1) {
    output[index] = view.getInt16(index * 2, true) / 32768
  }
  return output
}

/**
 * 线性插值重采样。
 *
 * Args:
 *   samples: 输入样本。
 *   sourceRate: 输入采样率。
 *   targetRate: 输出采样率。
 *
 * Returns:
 *   目标采样率样本；输入为空或采样率非正时返回空数组。
 */
export function resampleLinear(
  samples: Float32Array,
  sourceRate: number,
  targetRate: number,
): Float32Array {
  if (samples.length === 0 || sourceRate <= 0 || targetRate <= 0) {
    return new Float32Array(0)
  }
  if (sourceRate === targetRate) return samples.slice()

  const ratio = sourceRate / targetRate
  const length = Math.max(1, Math.floor(samples.length / ratio))
  const output = new Float32Array(length)
  for (let index = 0; index < length; index += 1) {
    const position = index * ratio
    const left = Math.floor(position)
    const right = Math.min(left + 1, samples.length - 1)
    const fraction = position - left
    output[index] = samples[left] * (1 - fraction) + samples[right] * fraction
  }
  return output
}

/**
 * 采集侧重采样并转成 PCM16。
 *
 * Args:
 *   samples: 源采样率浮点样本。
 *   sourceRate: 源采样率（AudioContext.sampleRate）。
 *   targetRate: 目标采样率，默认模型输入 16000。
 *
 * Returns:
 *   目标采样率的 Int16 PCM。
 */
export function toInputPcm16(
  samples: Float32Array,
  sourceRate: number,
  targetRate = KB_INPUT_SAMPLE_RATE,
): Int16Array {
  return float32ToPcm16(resampleLinear(samples, sourceRate, targetRate))
}
