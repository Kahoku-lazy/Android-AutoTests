/**
 * [P0] 知识库助手 PCM 转换与重采样 — 纯函数，不依赖 Web Audio。
 */
import { describe, expect, it } from "vitest"
import {
  clamp16,
  float32ToPcm16,
  pcm16ToFloat32,
  resampleLinear,
  toInputPcm16,
} from "@/modules/knowledge-assistant/audio/pcm"

describe("[P0] PCM 转换", () => {
  it("夹取值落在 Int16 范围内", () => {
    expect(clamp16(0)).toBe(0)
    expect(clamp16(40000)).toBe(32767)
    expect(clamp16(-40000)).toBe(-32768)
    expect(clamp16(Number.NaN)).toBe(0)
  })

  it("Float32 转 Int16 保留长度并按满量程缩放", () => {
    const pcm = float32ToPcm16(new Float32Array([0, 0.5, -0.5, 1, -1]))

    expect(pcm).toHaveLength(5)
    expect(pcm[0]).toBe(0)
    expect(pcm[1]).toBe(16384)
    expect(pcm[2]).toBe(-16383)
    expect(pcm[3]).toBe(32767)
    expect(pcm[4]).toBe(-32767)
  })

  it("Int16 转 Float32 做小端解码", () => {
    const source = new Int16Array([0, 32767, -32768])

    const floats = pcm16ToFloat32(source.buffer as ArrayBuffer)

    expect(floats).toHaveLength(3)
    expect(floats[0]).toBe(0)
    expect(floats[1]).toBeCloseTo(0.99997, 4)
    expect(floats[2]).toBe(-1)
  })

  it("奇数尾字节被忽略", () => {
    const buffer = new Uint8Array([0x00, 0x00, 0xff]).buffer as ArrayBuffer

    expect(pcm16ToFloat32(buffer)).toHaveLength(1)
  })
})

describe("[P0] 重采样", () => {
  it("48k 降到 16k 时长度按比例缩短", () => {
    const source = new Float32Array(4800).fill(0.5)

    const output = resampleLinear(source, 48000, 16000)

    expect(output).toHaveLength(1600)
    expect(output[0]).toBeCloseTo(0.5, 5)
    expect(output[1599]).toBeCloseTo(0.5, 5)
  })

  it("8k 升到 16k 时长度翻倍", () => {
    const source = new Float32Array(800).fill(-0.25)

    const output = resampleLinear(source, 8000, 16000)

    expect(output).toHaveLength(1600)
    expect(output[100]).toBeCloseTo(-0.25, 5)
  })

  it("空输入与非法采样率返回空数组", () => {
    expect(resampleLinear(new Float32Array(0), 48000, 16000)).toHaveLength(0)
    expect(resampleLinear(new Float32Array(10), 0, 16000)).toHaveLength(0)
  })

  it("采集链路输出目标采样率的 PCM16", () => {
    const pcm = toInputPcm16(new Float32Array(4800).fill(0.5), 48000, 16000)

    expect(pcm).toHaveLength(1600)
    expect(pcm[0]).toBe(16384)
  })
})
