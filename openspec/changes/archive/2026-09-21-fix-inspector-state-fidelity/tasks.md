## 1. 失败原因如实呈现

- [x] 1.1 `store.ts` 引入共享 `formatApiError`，8 个 action 的 catch 分支改为取其净化结果（保留后端 message），并保留原 `data.message` 分支作为异常 2xx 兜底；验证：`store.ts` 内固定文案 `ElMessage.error('` 命中 **0**、`formatApiError` 引用 **5** 处（import + `setError` + 保存 / 删除 / 页面回看三个不走横幅的写读路径）；异常 2xx 兜底分支仍在（`setError(source, data.message, 回退文案)`）
- [x] 1.2 `error` 改为 `{ message, source }`（`source ∈ capture / devices / snapshots / snapshot / analyze`，另记 `lastFailedSnapshotId`）；`index.vue` 的错误条绑定 `.message`；`clearErrorFor(source)` 在同一来源成功后撤掉提示；**同时删除了被 retry 取代的 `clearError`**（否则它当场变成新死代码）；验证：检索 `clearError` 命中 0（仅剩 `clearErrorFor`）
- [x] 1.3 `retry()` 按 `source` 重发（devices / snapshots / capture / snapshot / analyze，后者先确保快照已载入）；`index.vue` 的 `@retry` 指向 `store.retry()`；验证：真机走查（`temps/inspector-retry-check.mjs`，拦 `/api/devices/` 返回 500 后端 message）→ 错误条显示「设备列表加载失败（真机模拟：后端原因）」而非通用文案；放行后点「重试」→ `/api/devices/` 请求数 **1 → 2**、错误条消失、0 pageerror

## 2. 删除当前快照后回到空态

- [x] 2.1 `deleteSnapshot` 在删除的是当前快照时同时清 `analysis` 与 `selected`；验证：该分支含 `analysis.value = null` / `selected.value = null` / `clearChecked()`，并附注释说明「否则结构面板会继续渲染已删快照的分区与元素行」
- [x] 2.2 真机走查（`temps/inspector-state-check.mjs`）：载入一条 82 元素快照（表体 7 行、计数 82/82、分区非空）→ 在抽屉删除它 → 分区「暂无分区数据」、表体「未选中设备…」、表体行数 **7 → 0**、工具条计数消失、手机屏幕回无快照空态；验证：0 console error / 0 pageerror

## 3. 快照列表如实反映总量

- [x] 3.1 `SnapshotListDrawer.vue` 顶部显示总数并在截断时标明范围；验证：真机读数「共 272 条 · 已显示最近 100 条」（列表 100 项），删除一条后变为「共 271 条 · 已显示最近 100 条」

## 4. 首个 store 单测

- [x] 4.1 新增 `frontend/tests/device-inspector/p0/store.spec.ts`：① 409 时 `ElMessage.error` 收到后端 message 且 `error.source === 'capture'`；② `retry()` 使 `apiGetSnapshots` 被调用 2 次且错误清空；③ 删除当前快照后 `analysis`/`selected` 为 `null`、`filteredAnalysisElements` 长度 0；验证：`npx vitest run tests/device-inspector` → **Test Files 1 passed / Tests 3 passed**
- [x] 4.2 更新 `frontend/tests/README.md` 的 device-inspector 行；验证：该行由「— | ⬜ 未开始 | 0 | 0」改为「`tests/device-inspector/` | 🚧 P0 | 1 | 0 | 失败原因呈现 / 重试重发 / 删除当前快照后状态复位」

## 5. 门禁与归档

- [x] 5.1 `openspec validate fix-inspector-state-fidelity --strict`；验证：`Change 'fix-inspector-state-fidelity' is valid`（1 改 2 增的 delta 齐备）
- [x] 5.2 `npm run lint:styles`；验证：`LINT_EXIT=0`，批 1 / 1b / 2 / 3 / 4 全通过
- [x] 5.3 `npx vite build` 退出码 0；验证：`✓ built in 57.03s`
- [x] 5.4 检索全仓对旧文案的断言；验证：`frontend/tests` 与 `tests/` 对「获取失败 / 保存失败 / 快照加载失败 / 结构分析失败 / 页面加载失败」命中均为 **0**，无需同步
- [x] 5.5 划界核对；验证：本单改动 = `store.ts`（错误分支 + retry + `deleteSnapshot`）/ `index.vue`（错误条绑定）/ `SnapshotListDrawer.vue`（总数）+ 新增 `tests/device-inspector/p0/store.spec.ts` + `tests/README.md`；不含 `ScreenshotView*` / `SavedPagePicker.vue` / `constants.ts`；`store.ts` 的 hunk 与另两单不同行
