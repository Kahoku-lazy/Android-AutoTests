/**
 * log-keyword-colors — 日志关键词表：按「功能模块」分配色相（纯函数，无副作用）
 *
 * 分配规则：按模块在表里**首次出现的顺序**依次取色池，色池用完才循环。
 * 这样同一张表内不同模块互不撞色（只要模块数 ≤ 色池容量），且切换搜索词时已有配色不漂移。
 * 色相全部取 tokens.css 的模块令牌，本模块不写字面色值；深色由消费方与墨色混合得到。
 */

/** 模块色相池：只用已登记的模块令牌（顺序固定，改了会让既有配色整体挪位） */
export const MODULE_COLOR_TOKENS = [
  "var(--c-device)",
  "var(--c-workflow)",
  "var(--c-element)",
  "var(--c-ops)",
  "var(--c-case)",
  "var(--c-ai)",
  "var(--c-account)",
  "var(--c-task)",
] as const

/**
 * 把「模块名 → 颜色令牌」建成一张表，按首次出现顺序取色。
 *
 * Args:
 *   modules: 表格全部行的模块名序列（**过滤前**的全量，保证搜索时配色不漂移）；
 *     允许重复与空串，空串归入首个空模块的色相。
 *
 * Returns:
 *   模块名到 `var(--c-*)` 的映射；未出现的模块不在表内。
 */
export function buildModuleColorMap(modules: string[]): Map<string, string> {
  const map = new Map<string, string>()
  for (const raw of modules) {
    const module = (raw || "").trim()
    if (map.has(module)) continue
    map.set(module, MODULE_COLOR_TOKENS[map.size % MODULE_COLOR_TOKENS.length])
  }
  return map
}

/**
 * 取某个模块的颜色令牌；命中不到时回落（调用方通常先建好整张表）。
 *
 * Args:
 *   map: `buildModuleColorMap` 的产物。
 *   module: 功能模块名。
 *   fallback: 未命中时的令牌，默认次级文字色。
 *
 * Returns:
 *   已登记令牌的 `var()` 引用。
 */
export function moduleColorOf(
  map: Map<string, string>,
  module: string,
  fallback = "var(--app-text-secondary)",
): string {
  return map.get((module || "").trim()) || fallback
}
