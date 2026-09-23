## 1. 名称列显示别名

- [x] 1.1 `store.ts` 的 `viewSavedPage` 元素映射补 `alias: e.alias`；验证：真机回看页面 `#39`（「设备页面」，12 个元素全部带别名）时名称列显示中文别名，与 `/api/inspector/pages/39/` 返回的 `alias` 逐行一致（首屏 7 行全部匹配：设备 / 分布式网关入口 / 添加设备入口 / 搜索 …）
- [x] 1.2 `StructureAnalysisPanel.vue` 的 `nameValue()` 改为 `nameOverrides[_idx] ?? row.alias ?? (row.text || '')`；验证：同一次走查中名称列读数与服务端别名一致；快照模式下 `row.alias` 为 `undefined`，行为不变（见 3.4）

## 2. 回看态名称只读

- [x] 2.1 新增 `canRename = computed(() => !!store.snapshot?.snapshot_id)`；`startEdit` 首行守卫、模板去掉 `role/tabindex`、编辑图标 `v-if`、空名占位由「点击命名」改为「—」、光标改 default；验证：真机回看态单击名称格 → `.sap-name-input` 出现 **0** 个、编辑图标 **0** 个；快照态单击 → 出现 **1** 个输入框（改名仍可用）

## 3. 门禁与归档

- [x] 3.1 `openspec validate fix-inspector-saved-page-alias --strict`；验证：valid
- [x] 3.2 `npm run lint:styles`；验证：`LINT_EXIT=0`
- [x] 3.3 `npx vite build`；验证：退出码 0，✓ built in 45.52s
- [x] 3.4 真机两种模式回归（`temps/inspector-alias-check.mjs`）：回看态别名显示 + 不可改；快照态可进入改名；0 pageerror
- [x] 3.5 与 `fix-inspector-state-fidelity` 划界核对；验证：本单只动 `store.ts` 的 `viewSavedPage` 映射与 `StructureAnalysisPanel.vue`（名称取值/只读），不含错误分支、抽屉、`ScreenshotView*`、`constants.ts`
