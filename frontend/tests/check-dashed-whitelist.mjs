import { readdirSync, readFileSync, statSync } from "node:fs"
import { dirname, join, relative } from "node:path"
import { fileURLToPath } from "node:url"

const FRONTEND = join(dirname(fileURLToPath(import.meta.url)), "..")
const SRC = join(FRONTEND, "src")
const EXTS = [".vue", ".css"]

const OWNERS = new Set([
  "modules/ai-assistant/components/AgentRouteCard.vue",
  "modules/ai-assistant/components/AssistantCard.vue",
  "modules/ai-assistant/components/AssistantLanePanel.vue",
  "modules/ai-assistant/components/ThreadLogPanel.vue",
  "shared/components/SectionDivider.vue",
  "shared/styles/sketched-kit.css",
])

const BASELINE = new Map([])

function walk(dir, exts) {
  const out = []
  for (const name of readdirSync(dir)) {
    const full = join(dir, name)
    if (statSync(full).isDirectory()) out.push(...walk(full, exts))
    else if (exts.some((ext) => name.endsWith(ext))) out.push(full)
  }
  return out
}

const hits = []
for (const file of walk(SRC, EXTS)) {
  const rel = relative(SRC, file).split(/[\\/]/).join("/")
  if (OWNERS.has(rel)) continue
  const count = (readFileSync(file, "utf8").match(/dashed/gi) || []).length
  if (count > 0) hits.push({ rel, count })
}

const over = hits.filter((hit) => hit.count > (BASELINE.get(hit.rel) || 0))
const total = hits.reduce((sum, hit) => sum + hit.count, 0)

console.log(
  `[dashed] 虚线出现在 ${hits.length} 个文件 / ${total} 处（白名单组件 ${OWNERS.size} 个，存量登记 ${BASELINE.size} 个文件）`,
)

if (over.length) {
  console.error(`[dashed] 硬门禁失败：${over.length} 处新增虚线`)
  for (const hit of over) {
    console.error(
      `  ${hit.rel}：dashed ${hit.count} 次，基线 ${BASELINE.get(hit.rel) || 0} 次` +
        " → 虚线只属于 OWNERS 里登记的组件，其余改 1px solid",
    )
  }
  process.exit(1)
}

console.log("[dashed] 通过：虚线只出现在白名单组件与已登记存量内")
