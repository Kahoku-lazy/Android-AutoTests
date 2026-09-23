## 1. 零消费声明清理（constants.ts / store.ts）

- [x] 1.1 删除 `constants.ts` 的 `TABLE_HEADER_HEIGHT_PX` / `TABLE_ROW_HEIGHT_PX`；验证：全仓检索两标识符在 `device-inspector/` 内命中 **0**（仅剩 `device-pool/constants.ts` 与 `DevicePoolView.logic.ts`）；`constants.ts` 现 24 行
- [x] 1.2 删除 `store.ts` 的 `analyzing`（声明 / `analyzeSnapshot` 置位 / `finally` / `return` 暴露）；验证：`frontend/`（排除 node_modules 与文档）检索 `analyzing` 命中 **0**
- [x] 1.3 从 `store.ts` 的 `return` 中移除 `devices`（保留 ref 本体）；验证：`store.devices` 在模块内命中 **0**，`availableDevices` 仍过滤 `devices.value`
- [x] 1.4 `KEY_DISABLED_MESSAGE` 去掉 `export`；验证：`export const KEY_DISABLED_MESSAGE` 命中 **0**，标识符总命中 **2**（第 40 行声明 + 第 384 行使用）
- [x] 1.5 删除 `toggleCheck` 的 `?? row.__uid`；验证：全仓检索 `__uid` 命中 **0**
- [x] 1.6 **保留** `snapshotTotal`；验证：模块内 4 处命中 = 声明 / `fetchSnapshots` 赋值 / `return` 暴露 / **`SnapshotListDrawer.vue:36` 的消费**（由已归档的 `fix-inspector-state-fidelity` 显示「共 N 条 · 已显示最近 M 条」）

## 2. 死 CSS 与无效 CSS 声明清理

- [x] 2.1 删除 `ScreenshotView.css` 的 `.no-signal--error .no-signal__title`；验证：全仓检索 `no-signal--error` 命中 **0**
- [x] 2.2 删除 `.no-signal__icon` 的 `font-size: var(--app-size-2xl)`（保留 `opacity`）；验证：该块只剩 `opacity: 0.7`；真机读数图标 `svg` 计算宽度仍为 **32px**、`opacity` 仍为 `0.7`
- [x] 2.3 删除 `SaveToElementsDialog.vue` 的 `.save-hint`；验证：全仓检索 `save-hint` 命中 **0**，`<style scoped>` 无残留空规则（第 144-147 行）

## 3. 门禁与验收

- [x] 3.1 逐项静态复验（1.1–1.5 + 2.1–2.3）：除 1.6 说明的 `snapshotTotal` 外全部为 0；验证：见各任务读数
- [x] 3.2 `npm run lint:styles`；验证：`LINT_EXIT=0`（批 1 / 1b / 2 / 3 / 4 全通过）
- [x] 3.3 `npx vite build`；验证：退出码 0，`✓ built in 1m 15s`
- [x] 3.4 `npx vue-tsc --noEmit`；验证：错误集中在 4 个无关文件（`tests/dashboard/p0/useDashboardStats.spec.ts` 12、`tests/dashboard/p1/DashboardView.logic.spec.ts` 8、`tests/dashboard/p1/ModuleNavigator.spec.ts` 7、`src/modules/case-manager/components/ProjectTree.vue` 3），**`device-inspector` 0 条**
- [x] 3.5 真机渲染走查（`temps/inspector-purge-render-check.mjs`）：无快照空态 `svg` 32px / `opacity 0.7` / 文案「暂无页面快照」、两个光环节点在；快照抽屉显示「共 272 条 · 已显示最近 100 条」（列表 100 项）；「保存到元素定位」弹窗渲染正常（1 个级联、页面选择、确认键各就位）；0 console error / 0 pageerror
- [x] 3.6 范围核对：本单实际只改 **4 个文件**——`constants.ts`、`store.ts`、`components/ScreenshotView.css`、`components/SaveToElementsDialog.vue`（mtime 均为 17:19:40）；**不含 `ScreenshotView.vue`**（watcher 合并已按评审移入 `fix-saved-page-shot-basis`）。注：工作区含其他在途改动，`git diff --stat` 无法隔离本单，故以「改动文件 mtime + 逐项符号检索」为判据
- [x] 3.7 与另两单的改动点核对：`deleteSnapshot` 的 `analysis/selected` 复位仍在、`viewSavedPage` 的 `alias: e.alias` 仍在、`formatApiError(e, '删除失败')` 仍在 —— 三处互不重叠；验证：逐项 grep 命中符合预期
- [x] 3.8 编码与方式核对：全部改动由 `edit` 定点完成，无脚本批量改写；读回 `store.ts:39-40`、`SaveToElementsDialog.vue:144-147` 中文字符正常无乱码

## 4. 附带发现（未在本单处理，另记）

- 真机走查发现 `[data-testid="save-folder-cascader"]` 未出现在 DOM（`el-cascader` 不转发 `data-*`），而 `save-page-select` / `save-confirm-btn` 正常 —— 属既有 e2e 选择器缺口，与本单删除项无关，已登记待办
