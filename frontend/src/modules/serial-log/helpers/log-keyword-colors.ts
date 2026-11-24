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

export function buildModuleColorMap(modules: string[]): Map<string, string> {
  const map = new Map<string, string>()
  for (const raw of modules) {
    const module = (raw || "").trim()
    if (map.has(module)) continue
    map.set(module, MODULE_COLOR_TOKENS[map.size % MODULE_COLOR_TOKENS.length])
  }
  return map
}

export function moduleColorOf(
  map: Map<string, string>,
  module: string,
  fallback = "var(--app-text-secondary)",
): string {
  return map.get((module || "").trim()) || fallback
}
