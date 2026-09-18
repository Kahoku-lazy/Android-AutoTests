## 1. 常量唯一真相源（②）

- [x] 1.1 `report-generator/constants.ts`：`TABLE_HEADER_HEIGHT` 改为 45、`TABLE_ROW_HEIGHT` 改为 41（对齐唯一消费方现值），`PAGE_SIZE_OPTIONS` 改为 `[10, 20, 50, 100]`；验证：三个常量各有真实消费方
- [x] 1.2 `report-generator/ReportDetail.vue`：删除本地三个常量，改为从 `./constants` 导入；验证：`usePagination` 的 `options` 与 `tableScrollY` 仍取同值，`vue-tsc` 无错
- [x] 1.3 `report-generator/index.vue`：从 `./constants` 导入 `PAGE_SIZE_OPTIONS`，从 `usePagination` 解构中移除同名项，`options` 传该常量；验证：模板分页按钮仍渲染，列表页新增「20」档

## 2. 移除误导星号（③）

- [x] 2.1 `ai-assistant/components/AgentBasicInfo.vue`：移除名称项的 `required`；验证：全仓 `<el-form-item[^>]*\brequired` 命中 0

## 3. 规格与速查同步

- [x] 3.1 以 MODIFIED 更新 `specs/frontend-l4-data-surface/spec.md` 的两条需求（分页新增「选项集唯一」场景；表单校验的债务场景改为全仓 0 处）；验证：`openspec validate --strict` 通过
- [x] 3.2 更新 `frontend/AGENTS.md` L4 速查 §⑥：`required` 判据由 1 改为 0，新增 `PAGE_SIZE_OPTIONS` 同源判据；已知缺口移除 ②③，只留 3 处原生 `el-table`（并注明另由 `extend-apptable-capabilities` 处理）；验证：速查与 spec 一致

## 4. 门禁与归档

- [x] 4.1 `cd frontend && npm run typecheck`；验证：全仓 34 个既有错误，改动文件零错误
- [x] 4.2 用 `vue-frontend-check` 过改动文件；验证：改动行无新增违规
- [x] 4.3 归档（经 `openspec-archive-change`）；验证：`openspec/specs/frontend-l4-data-surface/spec.md` 已更新，变更进入 archive
