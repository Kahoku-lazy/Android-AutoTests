/**
 * 线型白名单门禁：虚线只属于 KpiCard 与 AgentRouteCard 两个组件。
 *
 * 规则真相源：.agents/skills/doodle-craft/SKILL.md §线型规则
 *   - 虚线是组件皮肤，不是页面装饰；判定看组件，不看页面/功能
 *   - 只有 shared/components/KpiCard.vue 与 modules/ai-assistant/components/AgentRouteCard.vue 可声明 dashed
 *   - 其余卡片、容器、分隔、轮廓一律 `1px solid color-mix(in srgb, var(--ink) 10%, transparent)`
 *
 * 迁移未完成，存量按「文件 → 次数」登记：只降不增。
 * 新文件出现 dashed、或既有文件次数超过基线 → exit 1。
 *
 * 用法：node tests/check-dashed-whitelist.mjs（npm run lint:lines）
 */
import { readdirSync, readFileSync, statSync } from "node:fs"
import { dirname, join, relative } from "node:path"
import { fileURLToPath } from "node:url"

const FRONTEND = join(dirname(fileURLToPath(import.meta.url)), "..")
const SRC = join(FRONTEND, "src")
const EXTS = [".vue", ".css"]

/** 唯一允许虚线皮肤的两个组件 */
const OWNERS = new Set([
  "shared/components/KpiCard.vue",
  "modules/ai-assistant/components/AgentRouteCard.vue",
])

/** 存量登记（只降不增）；改到某个文件时把对应行删掉，不要调大数字 */
const BASELINE = new Map([
  ["modules/case-manager/CaseFileSheet.style.css", 2],
  ["modules/dashboard/components/ActivityTimeline.vue", 1],
  ["modules/dashboard/DashboardView.style.css", 2],
  ["modules/device-pool/components/DisconnectDialog.vue", 1],
  ["modules/knowledge-assistant/components/TranscriptPanel.style.css", 1],
  ["modules/knowledge-assistant/components/VoiceConsole.style.css", 2],
  ["modules/serial-log/components/WifiPortPanel.style.css", 1],
  ["modules/task-list/components/CaseImportCard.vue", 1],
  ["modules/task-list/components/StepLogCheck.style.css", 1],
  ["modules/task-list/components/StepLogEvidence.style.css", 1],
  ["modules/task-list/components/TaskAttemptCard.vue", 1],
  ["modules/task-list/components/TaskMediaThumb.style.css", 2],
  ["modules/workflow/components/vueflow/PageFlowNode.vue", 2],
  ["modules/workflow/components/WorkflowDirTree.vue", 2],
  ["shared/components/AppCard.vue", 3],
  ["shared/components/AppSidebar.style.css", 1],
  ["shared/components/DoodleNote.vue", 2],
  ["shared/components/SketchCard.vue", 2],
  ["shared/styles/tokens.css", 2],
  ["shared/styles/workbench-theme.css", 4],
  ["views/LoginView.style.css", 1],
  ["style.css", 2],
])

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
        " → 虚线只属于 KpiCard / AgentRouteCard，其余改 1px solid",
    )
  }
  process.exit(1)
}

console.log("[dashed] 通过：虚线只出现在白名单组件与已登记存量内")
