## 1. 事实复核

- [x] 1.1 复核 64px 死声明；验证：全仓唯一渲染 `empty-state__icon` 的是 `shared/components/patterns/EmptyState.vue:3`，其 `<style scoped>` 的 `.empty-state__icon{font-size:40px}`（选择器叠加组件作用域属性，权重 0,2,0）恒高于 `tokens.css` 的全局规则（0,1,0）→ 64px 永不生效（`opacity` / `margin-bottom` 不受影响，故只删字号声明）
- [x] 1.2 复核等值关系；验证：`tokens.css` 字号刻度 `--app-size-xs: 12px` · `--app-size-sm: 14px`，与待换的 `12px` / `14px` 完全相等
- [x] 1.3 复核 6 处 `gap:14px`；验证：5 处 CSS 规则（`report-generator/index.vue` · `WorkflowFileBrowser.vue` · `ChatView.css` · `AgentBasicInfo.vue`）+ 1 处模板内联 style（`EvaluatorTab.vue:450`）

## 2. 代码改写

- [x] 2.1 `tokens.css` 删死声明；验证：`.empty-state__icon { opacity:0.5;margin-bottom:var(--app-space-sm); }`（`font-size:64px;` 已移除，替换计数 1）
- [x] 2.2 等值换令牌 7 处；验证：`AppSidebar.style.css` 14px ×2 → `--app-size-sm` · `ProjectTree.vue` 14px ×1 → `--app-size-sm` · `ProjectTree.vue` 12px ×2 与 `CaseFileSheet.vue` 12px ×2 → `--app-size-xs`（逐处左右值相等）
- [x] 2.3 不等值字号 4 处；验证：`AppSidebar.style.css` `11px` ×2 → `--app-size-xs`(12px) · `13px` → `--app-size-xs` · `15px` → `--app-size-md`(16px)
- [x] 2.4 间距 6 处；验证：全部替换为 `var(--app-space-md)`；改动文件内 `gap:\s*14px` 命中 **0**

## 3. 例外口径登记

- [x] 3.1 `tokens.css` 字号刻度注释；验证：新增两行，写明「文本字号必须取本刻度」+「例外：图形/展示级字号 18 / 40 / 96px」+ 判定语与出处
- [x] 3.2 `frontend/AGENTS.md` 硬性规范第 14 条；验证：条文含刻度来源、最小 12px、图形/展示级例外（此前 AGENTS 完全没有字号条款）
- [x] 3.3 `calibration.md` §2；验证：字号判罚补「例外：18 / 40 / 96px 可用字面量」，并把两处失效指针 `frontend/AGENTS.md §2` 改为「硬性规范 §1.14 + `tokens.css` 刻度注释」；同步修正 `vue-frontend-check/SKILL.md:16` 的同一指针

## 4. 报告同步

- [x] 4.1 L3 报告；验证：§五「裸 px 间距 6 处（挂起）」改为已收敛并附变更名；§七「唯一挂起项」改写为本变更记录
- [x] 4.2 L2 报告；验证：§五 gap 条目改为已收敛；§六「仍未做」撤掉 gap 项并改述为已收敛；footer 补 `close-typography-spacing-debt`
- [x] 4.3 `frontend/AGENTS.md` L3 速查 §⑥；验证：已知缺口里的「`gap:14px` 是裸 px（未收敛）」改为「已收敛 + 图形字号例外见 §1.14」

## 5. 门禁与验证

- [x] 5.1 `npm run typecheck`；验证：exit 2，34 个错误与上一轮逐文件一致（`tests/dashboard/p0|p1` ×27 · `device-inspector/store.ts` ×4 · `case-manager/components/ProjectTree.vue` ×3 的既有 TS2322/TS2353）。⚠️ 订正：改动文件并非全部 0 命中 —— `ProjectTree.vue` 已带着 3 个**既有**类型错误（`el-tree` 的 allow-drag / allow-drop 签名不符，自 P3 批次① 起就在），本次只改其 `font-size`，未触碰该处；其余 8 个改动文件在日志中 0 命中
- [x] 5.2 `npx vite build --mode development`；验证：`✓ built in 2m 5s`
- [x] 5.3 `vue-frontend-check`（calibration §7 扫描，9 个改动文件逐个跑）；验证：`font-size:\s*\d+px` 在该批仅剩 `ProjectTree.vue:640` 的 **18px 图形字号例外**；`gap:\s*14px` 全仓 0；六.协议类扫描无新增；全仓裸 px 字号由 15 处降为 **3 处**（恰为登记的 3 个图形/展示级字号）
- [x] 5.4 浏览器核验清单已交用户（可见项 10 处：间距 6 + 字号 4）——见交付说明
