## 1. 复核（逐项证明 0 消费方）

- [x] 1.1 `.agent-card`：全仓仅 `motion.css:69,74` 两处（选择器自身），0 模板使用；验证：`agent-card` 全仓命中列表只有 motion.css 两行，删除后全仓 = 0
- [x] 1.2 `no-bg-anim`：全仓仅 `router.ts:34,36` + AGENTS.md 2 处，0 个 CSS 规则；验证：命中列表无任何 `.css` 文件；删除后全仓 = 0
- [x] 1.3 `toastSlideDown` / `.el-message--top`：EP dist CSS `el-message--top` 0 命中、全仓 `customClass` 0 处；验证：关键帧仅被该规则引用（`toastSlideDown` 全仓 2 处 → 删除后 0）
- [x] 1.4 `AppTabs` `leafAnimation` / `shadow`：`ac-tabs--` 全仓仅 `AppTabs.vue:15,16`（类名计算自身）、0 条 CSS 规则；传参仅 `report-generator/index.vue:277,278`；验证：删除后 `ac-tabs--` / `leaf-animation` 全仓 = 0（`leafAnimation` 仅剩 AGENTS.md 的新说明文字）
- [x] 1.5 `gap:14px`：`--app-space-*` 刻度为 4/8/12/16…，**无 14px** → 收敛即 2px 可见变化，移出本变更；验证：本变更 6 个源码文件 diff 均不含 `gap` 修改，全仓仍有 6 处（`report-generator/index.vue` · `workflow/components/WorkflowFileBrowser.vue` · `ai-assistant/ChatView.css` · `ai-assistant/components/AgentBasicInfo.vue` · `ai-assistant/EvaluatorTab.vue`）

## 2. 删除死代码

- [x] 2.1 `motion.css` 删 2 行 `.agent-card` 选择器段（保 `.el-card:not(.ac-card)` 规则）；验证：`agent-card` 全仓 0；`.wb-shell .el-card:not(.ac-card)` 与 `:hover` 两条规则仍在（`motion.css:69,73`）
- [x] 2.2 `router.ts` 删 `no-bg-anim` 增删块（注释 + if/else 共 6 行）；验证：`beforeEach` 现为 `const token = getToken()` → 鉴权跳转两段（`router.ts:30-36`），全仓 `no-bg-anim` = 0
- [x] 2.3 `style.css` 删 `@keyframes toastSlideDown` + `.el-message--top` 规则（5 行）；验证：两关键字全仓 0，`.el-message` 皮肤（`style.css:136-141`）保留
- [x] 2.4 `AppTabs.vue` 删 `leafAnimation` / `shadow` prop 与类名计算（`:class` 数组 → 静态 `class="ac-tabs"`）；验证：`ac-tabs--` 全仓 0，`.ac-tabs` 基础样式仍在 `workbench-theme.css:140-153`（10 处）
- [x] 2.5 `report-generator/index.vue` 删 `:leaf-animation="true"` / `:shadow="true"`；验证：`AppTabs` 的 props（`items` / `modelValue`）与传参一一对应，无白传
- [x] 2.6 `useFilterTabs.ts` 删 JSDoc 示例中已不存在的两个属性；验证：`useFilterTabs.ts:27` 现为 `<Tabs :items="filterTabs" v-model="activeFilter">`

## 3. 文档同步

- [x] 3.1 `frontend/AGENTS.md` 删 L0 §⑤ 的 `router.ts` 死开关行；验证：§⑤ 表现剩 3 行（`useSidebarResize` ×2 + `main.ts`），无 `no-bg-anim`
- [x] 3.2 `frontend/AGENTS.md` 删 L0 §⑥ 已知缺口中的 `body.no-bg-anim 无消费方`；验证：该句全仓 0 命中（首次 replace 因分隔符不含前导空格而静默未命中，已按 `·` 分段过滤后重做并复核）
- [x] 3.3 `frontend/AGENTS.md` 改写「跨模块共享文件 §4 AppTabs」注意条；验证：新文案为「两个 prop 已于 2026-09-14 删除（无对应 CSS，属白传；实测仅 `report-generator` 一处在传）；勿复活」

## 4. 门禁与静态验证

- [x] 4.1 运行 `cd frontend && npm run typecheck`；验证：**exit 2，错误集合与 P3 三批完全一致**（`tests/dashboard/p0|p1/*.spec.ts` 20 · `device-inspector/store.ts` 4 · `case-manager/ProjectTree.vue` 3 等共 34 个，既有 DTO/类型不匹配）；**本变更 6 个文件在日志中 0 命中**
- [x] 4.2 构建校验 `npx vite build --mode development`；验证：`✓ built in 2m 46s`，成功（含 `AppTabs.vue` 模板改动）
- [x] 4.3 用 `vue-frontend-check` 技能过门禁：calibration §7 全部强制扫描（8 条样式类 + 5 条逻辑/协议类）逐文件跑过 6 个变更文件；五.10 可点击可达：`report-generator/index.vue` 的 8 处 `@click` 全部落在 `el-button`/`button[type=button]`/`a[href]`/`KpiCard`（KpiCard 对可点击态自带 `role="button"` + `tabindex=0` + `@keydown`，`KpiCard.vue:92,93,95`）→ ✅；三.1/三.3：`index.vue:96` 的 `catch` 设置了可见 `error.value`（非静默吞错）→ ✅；命中项（hex/rgba · overflow · border-radius · 裸 px）均为既有内容，本变更新增声明 = 0
- [x] 4.4 静态复核：`agent-card` · `no-bg-anim` · `toastSlideDown` · `el-message--top` · `ac-tabs--` · `leaf-animation` 全仓 0 命中（`leafAnimation` 仅剩 AGENTS.md 说明文字）；`gap:14px` + `gap: 14px` 保留 6 处并登记为待定项（需可见性核验）
