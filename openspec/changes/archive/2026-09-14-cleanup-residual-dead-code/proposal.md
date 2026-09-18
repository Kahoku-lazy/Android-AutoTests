## Why

P3（死令牌）关单后，L0~L3 复查清单里还剩 **5 项「声明了却没有消费方」的死代码**。逐项核实（全仓扫描，排除 `node_modules` / `dist` / 已归档变更）：

| # | 位置 | 现象 | 核实结论 |
|---|------|------|----------|
| 1 | `shared/styles/motion.css:69,74` | `.wb-shell .agent-card` 选择器段 | 全仓 `agent-card` **仅此 2 处**（都是选择器本身，0 个模板/host 使用）；同规则的另一段 `.wb-shell .el-card:not(.ac-card)` 才是活的（`.el-card` 有 17 处） |
| 2 | `router.ts:32-37` | 路由切换增删 `body.no-bg-anim` | 全仓 `no-bg-anim` **仅 router.ts 2 处 + AGENTS.md 2 处**，**0 个 CSS 消费方** → 动画禁用的「性能优化」从未生效 |
| 3 | `style.css:142-146` | `@keyframes toastSlideDown` + `.el-message--top` | EP dist CSS 中 `el-message--top` **0 命中**（该 class 不是 EP 产出的）；全仓 `customClass` **0 处** → 无人挂这个类，规则与关键帧都不可达 |
| 4 | `shared/components/AppTabs.vue:5,6,15,16` | props `leafAnimation` / `shadow` 生成 `ac-tabs--leaf` / `ac-tabs--shadow` | 全仓 `ac-tabs--` **仅 AppTabs.vue 2 处（类名计算本身）**，**无任何 CSS 规则** → 两个 prop 永不改变外观；实际消费方只有 `report-generator/index.vue:277,278` 一处（AGENTS.md 原写「3 个模块」是错的） |
| 5 | 多处 `gap:14px` | 模块内裸 px 间距（6 处） | **本变更不动** —— 间距刻度里没有 14px，改成 `--app-space-md`(12)/`lg`(16) 会产生 2px 视觉变化，属可见变更，需浏览器核验后再定（见 design 决策 5） |

## What Changes

- `motion.css`：删 2 行死选择器段 `.wb-shell .agent-card` / `.wb-shell .agent-card:hover`，保留同规则的活选择器
- `router.ts`：删 `beforeEach` 里的 `no-bg-anim` 增删块（注释 + if/else 共 6 行）
- `style.css`：删 `@keyframes toastSlideDown` 与 `.el-message--top` 规则（共 5 行），保留 `.el-message` 皮肤
- `AppTabs.vue`：删 `leafAnimation` / `shadow` 两个 prop 声明与两段类名计算，`:class` 数组改为静态 `class="ac-tabs"`
- `report-generator/index.vue`：删 `:leaf-animation="true"` / `:shadow="true"` 两行传参
- `useFilterTabs.ts`：删 JSDoc 示例里已不存在的 `:leaf-animation="true" :shadow="true"`
- `frontend/AGENTS.md`：删 L0 §⑤ 的 `router.ts` 死开关行、删 §⑥ 已知缺口里的 `body.no-bg-anim 无消费方`、改写「跨模块共享文件 §4 AppTabs」的注意事项（prop 已删 + 纠正「3 个模块」为 1 处）
- **BREAKING**：无。5 项均 0 消费方 → 无视觉 / 行为变化
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- `frontend/AGENTS.md` 的 L0 §⑤ / §⑥ / 跨模块共享文件 §4（三处同步点）
- 文档位置说明：本项为死代码清理，无 PRD/架构/接口文档对应内容；`dev_docs` 与 `openspec/specs` 对本 5 项 0 提及（已全仓扫描确认）
- 前置变更：`2026-09-14-retire-deprecated-tokens` · `2026-09-14-retire-module-scoped-tokens` · `2026-09-14-retire-misc-tokens`（P3 三批）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 前端源码：`shared/styles/motion.css` · `router.ts` · `style.css` · `shared/components/AppTabs.vue` · `modules/report-generator/index.vue` · `shared/composables/useFilterTabs.ts`（净删除约 19 行）
- 约束文档：`frontend/AGENTS.md`（3 处）
- 验证：`npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check`（calibration §7 强制扫描）+ 「5 项关键字全仓 0 命中」静态复核
- 不影响：任何页面渲染与交互；`gap:14px`（6 处）按决策 5 不在本变更范围
