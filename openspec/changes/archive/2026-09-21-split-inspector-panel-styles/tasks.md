## 1. 样式层拆分

- [x] 1.1 把 `<style scoped>` 整块逐字抽到 `components/StructureAnalysisPanel.css`（241 行），`.vue` 改用 `<style scoped src="./StructureAnalysisPanel.css"></style>`；验证：`.vue` **624 → 381 行**（< 500），`.css` 241 行；拆分由「读取原文件逐行切片」完成，无手工转写（可 diff 对齐）

## 2. 真机核对（`:deep()` 是否仍生效）

- [x] 2.1 载入快照后计算样式：“`.el-table__body` 的 `min-width` = **986px**”“`.el-scrollbar__wrap` 的 `cursor` = **grab**”“行内复选框 `pointer-events` = **auto**”三项全部与拆分前一致；编译产物中确认 deep 规则已被作用域化：`.sap-table-body[data-v-56ec11b6] .el-scrollbar__wrap { cursor: grab; ... }`
- [x] 2.2 渲染与交互：表体 7 行 / 表头 8 列正常，缩略图与名称列正常，**0 pageerror**；验证：`temps/inspector-style-split-check.mjs` 读数

## 3. 门禁与归档

- [x] 3.1 `openspec validate split-inspector-panel-styles --strict`；验证：valid（`skip_specs` 生效）
- [x] 3.2 `npm run lint:styles`；验证：`LINT_EXIT=0`（含拆出的 `.css`）
- [x] 3.3 `npx vite build`；验证：退出码 0，✓ built in 1m 18s
- [x] 3.4 `npx vitest run tests/device-inspector`；验证：3 passed
- [x] 3.5 改动范围核对；验证：新增 `StructureAnalysisPanel.css` + 修改 `StructureAnalysisPanel.vue`，共 2 个文件
