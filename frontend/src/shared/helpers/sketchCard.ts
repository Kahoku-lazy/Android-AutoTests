/**
 * 撕纸入口卡的 cycle 配色 / 微倾（父级按 v-for index 注入）。
 * 令牌来自 tokens.css 的 8 个 --c-*，不写字面量色。
 */
export const SKETCH_TONES = [
  "var(--c-dashboard)",
  "var(--c-device)",
  "var(--c-element)",
  "var(--c-case)",
  "var(--c-runner)",
  "var(--c-report)",
  "var(--c-ai)",
  "var(--c-workflow)",
] as const

/** 对齐 principles 卡的 ±0.6°~1.5° 倾角循环 */
export const SKETCH_TILTS = [-1.5, 1, -0.6, 1.2, -1, 0.8, 0.4, -0.9] as const

export function sketchToneAt(index: number): string {
  if (!Number.isInteger(index) || index < 0) {
    throw new Error(`sketchToneAt: index 必须是非负整数，收到 ${index}`)
  }
  return SKETCH_TONES[index % SKETCH_TONES.length]
}

export function sketchTiltAt(index: number): number {
  if (!Number.isInteger(index) || index < 0) {
    throw new Error(`sketchTiltAt: index 必须是非负整数，收到 ${index}`)
  }
  return SKETCH_TILTS[index % SKETCH_TILTS.length]
}
