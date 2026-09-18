## 1. 覆盖层跳出包含块

- [x] 1.1 `frontend/src/views/components/LoginErrorOverlay.vue`：给 `el-dialog` 加 `append-to-body`，并在组件 JSDoc 补写「挂载点带 transform → 遮罩相对该容器解析（实测 424×403）」的原因。验证：模板中 `append-to-body` 存在；`:model-value` + `@update:model-value` 绑定写法未改动
- [x] 1.2 `frontend/src/views/LoginView.style.css`：在 `.meeting-doodle` 的 `transform: rotate(1.2deg)` 上方补登记注释（**只加注释**）。验证：`transform: rotate(1.2deg);` 仍在（`.meeting-doodle` 规则内，第 232 行起），值未变

## 2. 实测复验

- [x] 2.1 实拍复测（重跑 `temps/login-layer-map/login-layer-map.cjs`）：`.el-overlay` 实测 **1440×900 @ (0,0)**，等于视口；修复前为 424×403 @ (822,215)。`.el-dialog` 由「卡内 423×156 @ (824,350)」变为「视口居中 420×147 @ (510,135)」（510+420/2=720=1440/2，EP 默认 15vh 顶距 135=900×15%）
- [x] 2.2 对照复测：同一次运行注入 `transform: none` 后 `.el-overlay` = **1440×900 @ (0,0)**，与不注入时**完全一致** → 祖先 transform 已不再影响遮罩，因果被消除（修复前两者分别为 424×403 与 1440×900）
- [x] 2.3 视觉不回归：`.meeting-doodle` 仍带手绘倾斜；`verify-canvas-2.png` 确认遮罩铺满整页、弹层内容（「提示」/「用户名或密码错误」/「知道了」）与按钮文案未变
- [x] 2.4 证据产物同步：D 节结论区块改为**数据驱动**——遮罩等于视口即输出「已修复」文案，否则输出缺陷与根因。验证：重新生成的 `login-layer-map.html` 含「复验：L5 遮罩已覆盖整个视口」

## 3. 门禁与归档

- [x] 3.1 门禁：`npm run lint:styles` 通过；`npm run typecheck` 共 30 例错误但**登录/覆盖层相关为 0**（均为 dashboard/case-manager 既有问题）；`vitest --project login/p1` = 3 failed | 9 passed，与修复前**完全同数**（既有失败未恶化）
- [x] 3.2 顺带定位既有失败的根因：`LoginErrorOverlay.spec.ts` 的 3 例失败源于 **vitest 环境未注册 Element Plus 组件**——运行日志为 `[Vue warn]: Failed to resolve component: el-dialog / el-button`，故 `el-dialog` 渲染为未知元素、查不到 `.el-dialog` / `.el-overlay`。该 spec 是 L5 收敛前自建遮罩时代的遗留断言。按 Non-goals **本次不修**，仅登记
- [x] 3.3 `openspec validate fix-l5-overlay-transform-trap` 通过后归档；`specs/frontend-l5-overlay/spec.md` 主 spec 同步新增需求「Blocking overlays escape transformed ancestors」（含 3 个 Scenario）
