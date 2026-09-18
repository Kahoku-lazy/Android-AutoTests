## 1. 复核与基线

- [x] 1.1 复核 6 处点阵与 13 处 `.doc-body` 覆写清单 ✅（清单与 `报告-前端区域层级与L3现状复盘.html` §五 一致）；三档基线由用户在浏览器中代验 ✅（2026-09-14，768/1024/1280）

## 2. 点阵收敛

- [x] 2.1 删除 `.doc-page` 上 2 处点阵（`device-inspector/index.vue`、`dashboard/DashboardView.style.css`），纸面改纯纸色；验证：`rg -n "radial-gradient\(circle" frontend/src/modules` 0 命中（`ScreenshotView` 的 pushpin 渐变除外，需确认其非点阵）
- [x] 2.2 删除 `.doc-body` 上 4 处点阵（`case-manager/ProjectWorkspace.vue`、`element-locator` 的 ProjectWorkspace / ProjectList / LocatorFileView）；验证：同 2.1 命令 0 命中
- [x] 2.3 同步 `frontend/AGENTS.md` L2 速查 §③：移除「背景点阵」许可，改为「纸面为纯色，装饰只由 PaperDoodles 提供」；验证：文档不再允许 `.doc-body` 自绘点阵

## 3. 内边距对齐

- [x] 3.1 `frontend/src/style.css` 基座 `.doc-body` 水平内边距由 `var(--app-space-xl)` 改为 `var(--app-space-lg)`；验证：浏览器实测页头品牌区左边缘与首个内容块左边缘差值为 0（/dashboard、/reports、/reports/{runId}、/inspector、/elements）

## 4. 覆写收敛

- [x] 4.1 逐处收敛 5 处裸 `.doc-body` 覆写：与全局 / 策略② 等价者整条删除，含真实增量者改为 `.<模块modifier> .doc-body`；`report-generator/index.vue` 若保留增量须为其页面根补 modifier；验证：`rg -n "^\.doc-body \{" frontend/src/modules` 0 命中
- [x] 4.2 为 4.1 的每一处给出「删除」或「限定保留」的等价性说明（逐属性对照）；验证：说明覆盖全部 5 处，无遗漏

## 5. 画布例外登记

- [x] 5.1 在 `workflow/index.vue` 的 `.wb-body` 处加注释指向登记，并在 `frontend/AGENTS.md` 与 `openspec/specs/frontend-l3-container/spec.md` 保留例外条款；验证：`rg -n "wb-body" frontend/src/modules` 仍恒为 workflow 一处

## 6. 门禁与验收

- [x] 6.1 运行 `cd frontend && npm run typecheck`；验证：无本变更引入的新错误（既有无关报错需注明）
- [x] 6.2 构建校验 `npx vite build --mode development`；验证：构建成功
- [x] 6.3 用 `vue-frontend-check` 技能过一遍前端门禁（含二.2 硬编码色 / 二.7 间距 / 一.1 布局裁剪）；验证：逐项记录，无新增违规
- [x] 6.4 在 768 / 1024 / 1280 三档核验 6 个受影响页面；验证：**用户于 2026-09-14 在已登录浏览器中代验，结论为「点阵已消失、左边缘对齐、无双滚动条」均正常**（本环境无可用账号，故由用户执行；非静态替代口径）
