## Why

上一轮 `vue-frontend-check` 报告里还挂着两项样式债，本轮收口：

**二.1 字号未走令牌** —— 地毯式扫描发现 15 处裸 px `font-size`，其中报告点名的那条其实是**死声明**：

| 站点 | 值 | 判定 |
|------|----|------|
| `tokens.css` 的 `.empty-state__icon` | 64px | **死声明** —— 被 `EmptyState.vue:34` 的 scoped 规则（`.empty-state__icon` + 组件 data 属性，权重 0,2,0 对 0,1,0）恒压过；全仓只有该组件渲染此 class |
| `AppSidebar.style.css` | 11px ×2 | **真违规** —— 低于 `tokens.css` 明写的「字号最小 12px」 |
| `AppSidebar.style.css` 品牌标题 | 15px | 文本字号，无对应刻度 |
| `AppSidebar.style.css` 二级菜单标签 | 13px | 文本字号，同级主项为 14px |
| `ProjectTree.vue` / `CaseFileSheet.vue` / `AppSidebar.style.css` | 12px ×4 · 14px ×3 | 与刻度**等值**（`--app-size-xs` / `--app-size-sm`） |
| `ProjectTree.vue` 树节点图标 · `EmptyState.vue` 空态 emoji · `NotFound.vue` 404 数字 | 18px · 40px · 96px | **图形/展示级字号**，刻度里没有对应档 |

**二.7 裸 px 间距** —— `gap:14px` 6 处（5 个文件），刻度无 14px。实测同文件相邻规则（`report-generator/index.vue` 的 `.kpi-row` / `.chart-section`、`ChatView.css`、`EvaluatorTab.vue`）与全仓模块内 gap 用量（`--app-space-sm` 74 · `--app-space-md` 35 · `--app-space-xs` 26）都指向 **12px**。

两处都需要裁决，已确认：间距收敛到 `--app-space-md`（12px）；字号按「删死声明 + 等值换令牌 + 11px 提到 12px + 图形字号登记例外」，并把 13px 归 `--app-size-xs`、15px 归 `--app-size-md`。

## What Changes

**零视觉变化（可静态证明）**

- 删 `tokens.css` 的死声明 `font-size:64px`（保留同规则的 `opacity` / `margin-bottom`）
- 等值换令牌：`font-size: 12px` → `var(--app-size-xs)` ×4（`ProjectTree.vue` ×2 · `CaseFileSheet.vue` ×2）· `font-size: 14px` → `var(--app-size-sm)` ×3（`AppSidebar.style.css` ×2 · `ProjectTree.vue` ×1）

**可见变化（每处 ≤ 2px，需浏览器核验）**

- `gap:14px` ×6 → `var(--app-space-md)`（12px）：`report-generator/index.vue` · `workflow/components/WorkflowFileBrowser.vue` · `ai-assistant/ChatView.css` · `ai-assistant/components/AgentBasicInfo.vue` · `ai-assistant/EvaluatorTab.vue`（内联 style）
- `AppSidebar.style.css`：`11px` ×2 → `var(--app-size-xs)`（12px，达到文档下限）· `13px` → `var(--app-size-xs)`（12px）· `15px` → `var(--app-size-md)`（16px）

**口径登记（让例外可执行）**

- `tokens.css` 字号刻度注释：写明「文本字号必须取本刻度（最小 12px）；图形/展示级字号（树节点图标 18px · 空态 emoji 40px · 404 数字 96px）允许字面量」
- `frontend/AGENTS.md`「Vue 代码编写规范 1. 硬性规范」新增第 14 条：同上口径（此前「字号最小 12px」只写在 `tokens.css` 注释里，AGENTS 没有对应条款）
- `.agents/skills/vue-frontend-check/references/calibration.md` §2 字号行：补例外口径，并把失效指针「见 frontend/AGENTS.md §2」改为指向 AGENTS 第 14 条 + `tokens.css` 刻度注释

**文档同步**

- 两份现状复盘报告：把 `gap:14px` 6 处「挂起」改为已收敛并附本变更名；L3 §七 / L2 footer 补记本变更

- **BREAKING**：无（无接口/数据变更）；有**微小可见观感变化**（6 处间距 −2px、侧栏 2 处字号 +1px、1 处 −1px、1 处 +1px）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 令牌真相源：`frontend/src/shared/styles/tokens.css`（字号刻度 + 图形字号例外）
- 规则载体：`frontend/AGENTS.md`（新增第 14 条）· `.agents/skills/vue-frontend-check/references/calibration.md`（门禁量规）
- 现状复盘：`dev_docs/05-开发与测试/设计方案与报告/报告-前端区域层级与L2现状复盘.html` · `报告-前端区域层级与L3现状复盘.html`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 前端样式：`tokens.css` · `shared/components/AppSidebar.style.css` · `modules/case-manager/components/ProjectTree.vue` · `modules/case-manager/CaseFileSheet.vue` · `modules/report-generator/index.vue` · `modules/workflow/components/WorkflowFileBrowser.vue` · `modules/ai-assistant/ChatView.css` · `modules/ai-assistant/components/AgentBasicInfo.vue` · `modules/ai-assistant/EvaluatorTab.vue`
- 规则/文档：`frontend/AGENTS.md` · `calibration.md` · 两份 HTML 报告
- 验证：`npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check`（calibration §7 扫描）+ 用户浏览器核验可见项
