/**
 * 线型白名单门禁：虚线只属于已登记的组件落点。
 *
 * 规则真相源：.agents/skills/doodle-craft/SKILL.md §线型规则
 *   - 虚线是组件皮肤，不是页面装饰；判定看组件，不看页面/功能
 *   - 只有 shared/components 里的 AgentRouteCard.vue 可自行声明 dashed
 *     （KpiCard 已于 2026-11-09 按需求改为实线，移出白名单）
 *   - Sketched UI Kit（2026-11-16 新增分类）的虚线统一由
 *     shared/styles/sketched-kit.css 提供，作用域 .sketch-kit，仅限按钮描边态与输入框边框
 *   - 对话页运行日志卡（2026-11-16，需求方给参考图）：一轮一张虚线卡 + 顶部胶带，
 *     由 modules/ai-assistant/components/ThreadLogPanel.vue 自己声明
 *   - 页面分区虚线（2026-11-17，需求方批准新增落点）：两段并列内容之间的一条浅墨虚线，
 *     由 shared/components/SectionDivider.vue 自己声明；页面不得就地写 dashed
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

/** 允许虚线的落点：助手颜料片、助手对话栏面板、运行日志卡、页面分区线、手稿控件皮肤样式表 */
const OWNERS = new Set([
  "modules/ai-assistant/components/AgentRouteCard.vue",
  "modules/ai-assistant/components/AssistantCard.vue",
  "modules/ai-assistant/components/AssistantLanePanel.vue",
  "modules/ai-assistant/components/ThreadLogPanel.vue",
  "shared/components/SectionDivider.vue",
  "shared/styles/sketched-kit.css",
])

/** 存量已清零：任何非白名单文件出现 dashed 都直接阻断 */
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
