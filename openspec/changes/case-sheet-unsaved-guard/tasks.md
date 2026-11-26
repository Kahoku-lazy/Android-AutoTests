## 1. 文案常量与草稿差异判定

- [x] 1.1 新增 `frontend/src/modules/case-manager/constants.ts`：`UNSAVED_LEAVE_*`（标题 / 正文 / 「离开」「留下」）、`DISCARD_DRAFT_*`（标题 / 正文 / 「丢弃」「继续编辑」）与 `UNSAVED_GUARD_SKIP_PATHS`（登录页不二次拦截）；登出的 `LOGOUT_UNSAVED_*` 放在 `shared/helpers/logout.ts`。组件内不再出现提示文案字面量。验证：`npx eslint src/modules/case-manager` 0 问题。**验证结果**：eslint exit 0；prettier 全部合规。
- [x] 1.2 `helpers/sheet.ts` 增加 `hasDraftChanges(row, draft)`：两侧都过 `editablePayload()` 后做深比较，天然忽略 `step.id` / `updated_at`，并让「只差尾部空格」「空提示 `{}` 与缺键」不算改动。验证：`sheet.spec.ts` 补 7 条用例。**验证结果**：`npx vitest run --project case-manager/p1` 25 tests passed（新增 7 条：克隆等价、无草稿、改动作、增删步骤、改行字段、尾部空格、空提示）。
- [x] 1.3 抽屉把草稿脏状态算成 `hasEdits` 并以 `dirty-change` 上抛；关闭时草稿清空自动回落为 false。验证：真机点开抽屉不改动即关闭，页面「未保存」chip 不出现（见 4.1 第 1 条）。

## 2. 抽屉丢弃草稿前确认

- [x] 2.1 `SheetRowDrawer.vue` 挂 `:before-close="handleBeforeClose"`（✕ / 遮罩 / Esc 三条路径都经过它），并在 footer「取消」的 `close()` 里复用同一个 `confirmDiscardDraft()`；无改动时 MUST NOT 弹框。验证：真机 ✕ 两条路径。**验证结果**：未编辑点 ✕ → 抽屉直接关闭、无确认框；改动后点 ✕ → 确认框标题「有未应用的改动」，按钮「继续编辑 / 丢弃」；选「继续编辑」抽屉仍在且草稿逐字保留；选「丢弃」抽屉关闭且该行未变成未保存。
- [x] 2.2 丢弃草稿 MUST NOT 影响表格里已应用的行：`hasEdits` 只来自草稿与当前行比较，`dirtyIds` 不动。验证：同 2.1 的「丢弃后行未变脏」。

## 3. 离开守卫与退出登录

- [x] 3.1 新增 `modules/case-manager/composables/useUnsavedGuard.ts`：`isDirty` 传函数（避免快照过期）；`onMounted` 挂 `beforeunload`、`onBeforeUnmount` 摘掉；`onBeforeRouteLeave` 在脏时走 `confirmLeaveUnsaved()`，取消返回 `false` 留在原页。验证：`unsaved-guard.spec.ts`。**验证结果**：8 条用例全绿（不脏放行且不弹、确认后放行、取消返回 false、`confirmLeaveUnsaved` 取消映射、跳登录放行、`beforeunload` 挂载拦截 / 卸载不拦截、不脏不拦截、缓存页不拦截）。
- [x] 3.2 `ProjectSheet.vue` 接 `drawerDirty`，`hasUnsaved = dirtyCount > 0 || drawerDirty`，并挂 `useUnsavedGuard(() => hasUnsaved.value, () => route.fullPath === pagePath)`。**注意**：`App.vue` 的 `<router-view>` 外包着 `<keep-alive :max="5">`，页面缓存时不会卸载，`beforeunload` 必须按「本页是否仍是当前路由」判别，否则在别的页面刷新会被旧页面拦住。验证：真机「应用改动」后出现「未保存 1 处」，点面包屑「返回项目列表」弹确认，选「留下」停留原页且 chip 仍在；缓存页不拦截由单测守住。
- [x] 3.3 新增 `shared/composables/useUnsavedChanges.ts` 全局登记（`useUnsavedGuard` 内部调用，卸载自动撤销），暴露 `hasUnsavedChanges()` 供侧边栏读取。验证：`tests/shared/p0/unsaved-changes.spec.ts` 3 条。**验证结果**：登记 / 干净后撤销、卸载自动撤销、多页面互不覆盖。
- [x] 3.4 退出登录改为「先确认、后吊销」：`AppSidebar.logout()` 通过 `hasUnsavedChanges()` + `ElMessageBox` 先确认，再走 `runLogout({ hasUnsaved, confirmDiscard, revoke, clearSession, goToLogin, onRevokeError })`；取消时三项都不做。**过程中否掉了「先导航、后吊销」方案**：带 token 访问 `/login` 会被全局守卫改道 `/dashboard`，路由守卫因此二次弹确认，登出永远走不完（探针日志实证）；最终改为侧边栏确认 + 守卫对 `/login` 放行。验证：`tests/shared/p0/logout.spec.ts` 4 条顺序断言 + 真机（见 4.3）。**验证结果**：无脏不确认、脏则先确认、取消什么都不做、吊销失败仍清本地。

## 4. 浏览器真机复核（Playwright + 本机 chromium + 真实 JWT）

- [x] 4.1 抽屉与站内离开两组场景，全程未点「保存」，库中零写入：未编辑点 ✕ 直接关闭；改动后点 ✕ 弹「有未应用的改动」并可继续编辑或丢弃；应用改动后点「返回项目列表」弹「有改动还没有保存」，选「留下」停留原页且 chip 仍在；脏态 `reload()` 捕获到 `beforeunload` 原生对话框，取消后 URL 不变。**验证结果**：`temps/probe-guard.mjs` 20 项断言全部为期望值；截图 `temps/guard-dialog-drawer.png`、`temps/guard-dialog-route.png`。
- [x] 4.2 附带复核：用户在 17:47 按「应用改动 → 保存」重录的步骤已入库（两条用例各 2 步、`updated_at=17:47:02`），说明本次拦截只加提示、没有破坏原保存链路。
- [x] 4.3 退出登录真机复核：脏态点侧边栏「退出」→ 弹「有改动还没有保存」，按钮「留下 / 退出登录」；选「留下」后 URL 仍是 `/cases/projects/26`、零登出请求、token 仍在、chip 仍在；再点退出并选「退出登录」→ URL 变 `/login`、发出登出请求、token 已清。**验证结果**：`temps/probe-logout2.mjs` 11 项断言全部为期望值；截图 `temps/guard-logout-cancel.png`。

## 5. 门禁

- [x] 5.1 `npx vue-tsc --noEmit` exit 0；`npx eslint src/modules/case-manager tests/case-manager src/shared tests/shared` 0 error（3 条存量 `any` / 空块 warning 与本次无关）；`npx prettier --check`（模块 + 用例 + shared）全部合规；`node tests/check-style-gates.mjs` exit 0（批 1 / 1b / 3 / 4 全通过，存量裸色字面量 9 处未增加）。
- [x] 5.2 `npx vitest run`（全量前端）：95 个文件 / 603 tests 全绿。
- [x] 5.3 `npx vite build --outDir ../temps/vite-build-probe`：构建成功，未覆盖仓库内 `frontend/dist`。
- [x] 5.4 未跑 `python -m run check` 全量门禁的理由：工作区存在与本改动无关的在途变更（`switch-ui-font-to-harmonyos-sans`、ai-assistant eval 页面），全量门禁会混入他人 WIP 的失败；本次改动只碰用例表页面、侧边栏登出与 shared 两个小件，已按 5.1–5.3 逐项覆盖对应门禁项，并额外跑了真机浏览器复核（4.1–4.3）。

## 6. 文档

- [x] 6.1 契约写进 `openspec/changes/case-sheet-unsaved-guard/specs/case-project-sheet/spec.md`（MODIFIED「用例行编辑经独立面板」+ ADDED「未保存改动离开前必须提示」，含退出登录场景与「登录页不二次拦截」），不新增前端模块文档：`frontend/AGENTS.md` 的 case-manager 行保持「无模块文档」，口径以规格为准。
- [x] 6.2 备注：`beforeunload` 的提示文案由浏览器决定，各浏览器不可定制，只保证「会拦」；站内与退出的确认框文案可定制，已收进常量文件。

## 7. 已知边界与后续

- [x] 7.1 「401 自动跳登录要不要拦」已定：守卫对 `/login` 放行——会话已死时再问「要不要留下」没有意义。
- [ ] 7.2 被 `keep-alive` 缓存的旧项目页如果仍持有草稿，会在别处点「退出」时被计入未保存（按设计如此：缓存页的改动确实会丢）。若要更精细，可在退出确认里指出是哪个项目页。
- [ ] 7.3 登出 503-retry 分支：旧实现留在原页并保持登录，新实现提示后仍清本地会话并回登录页，避免半登录状态。已在 design.md 的 Risks 中登记。
- [ ] 7.4 抽屉宽度会盖住页面右上角的「保存」，本轮按用户要求只加离开提示、未动版式；若要一并解决，可在抽屉 footer 增加「应用并保存」或在抽屉内常驻显示未保存状态。
