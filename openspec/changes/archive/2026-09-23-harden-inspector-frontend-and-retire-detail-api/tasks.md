## 1. 共享登记处收敛

- [x] 1.1 新增 `frontend/src/shared/helpers/mediaUrl.ts`（`mediaUrl(path)`：空路径 → 空串，否则 `/media/{path}`），验证：`frontend/tests/shared/p0/mediaUrl.spec.ts` 2 条通过
- [x] 1.2 新增 `frontend/src/shared/helpers/deviceOccupancy.ts`（前缀清单 + `isRunnerOccupied(occupiedBy)` + `isExecutionOccupied(device)`），验证：`frontend/tests/shared/p0/deviceOccupancy.spec.ts` 5 条通过（`BUSY`+前缀 / `BUSY`+非前缀 / 非 `BUSY` / `occupied_by` 缺失）
- [x] 1.3 `device-inspector/store.ts` 删除自有 `mediaUrl` 与 `EXEC_PREFIXES`，改为引用共享件；`ScreenshotView.vue`、`StructureAnalysisPanel.vue` 的 `mediaUrl` import 改源，验证：`npx vitest run tests/device-inspector` 全绿
- [x] 1.4 `element-locator/helpers/elementPresentation.ts` 删除本地拼接（消费点改引共享件），`ai-assistant/helpers/task-detail.ts` 复用共享拼接并保留绝对 URL / `data:` / `/` 直通分支，验证：`npx vitest run tests/element-locator tests/ai-assistant` 全绿
- [x] 1.5 `device-pool/constants.ts` 删除 `RUNNER_OCCUPIED_PREFIXES` 定义，`DeviceCard.vue` / `DeviceActionsCell.vue` 改用 `isRunnerOccupied`，`DeviceStatusCell.vue` 改用 `isExecutionOccupied`，验证：`npx vitest run tests/device-pool` 全绿
- [x] 1.6 扫描确认唯一登记：`frontend/src` 内 `/media/` 拼接字面量只剩 `shared/helpers/mediaUrl.ts` 一处；执行引擎占用前缀清单只剩 `shared/helpers/deviceOccupancy.ts` 一处（`useDevicePoolState.ts:93` 是 MOCK 造数，非登记处）
- [x] 1.7 验证依赖方向：`frontend/src/shared/helpers` 内 `@/modules/` 零命中

## 2. 截图几何纯函数与单测

- [x] 2.1 新增 `frontend/src/modules/device-inspector/helpers/screenshotGeometry.ts`（`boxOf`：`coords` / `x,y,w,h` / `bounds` 三形态，非法返回 `null`；`pickElementAt`：命中取面积最小者，宽高 ≤ 0 跳过），验证：`screenshotGeometry.spec.ts` 10 条通过
- [x] 2.2 `ScreenshotView.vue` 改为调用纯函数，DOM 基准换算（`getBoundingClientRect` / `displayScale`）保留在组件，验证：`npx vitest run tests/device-inspector` 全绿 + 抽取前后代码等价核对（画布实际绘制 jsdom 不可覆盖，真机 / 浏览器验收待人工）
- [x] 2.3 改写 `ScreenshotView.vue` 中仍以「已保存页面」解释尺寸兜底的过期注释，验证：模块内 grep「已保存页面」零命中

## 3. 保存弹窗用例

- [x] 3.1 新增 `frontend/tests/device-inspector/p0/SaveToElementsDialog.spec.ts`，用 `vi.mock('@/modules/element-locator/api')` 固定项目树，覆盖级联只含目录、末层目录页面列表、未选目录时列根下页面，验证：用例通过
- [x] 3.2 覆盖两条提交分支：已有页面提交 `pageId`；新建页面提交 `pageLabel + folderPath`（新建名默认取快照包名），验证：断言的入参形状与 `store.saveToElements` 契约一致
- [x] 3.3 覆盖必填规则登记与校验拦截：`rules` 含 `selectedPageId` / `newPageLabel` 的 `required`，`validate` reject 时 MUST NOT 调用 `store.saveToElements`，验证：用例通过（该文件 8 条全绿）

## 4. 快照详情端点退役

- [x] 4.1 删除 `tests/api/case/inspector.yaml` 的 TC-INS-003 与 TC-INS-030，验证：`python -m pytest tests/graybox/unit/test_api_path_callers.py -q` 7 passed
- [x] 4.2 删除 `apps/device_inspector/urls.py` 的 `snapshots/<int:snapshot_id>/` 路由与 `views.snapshot_detail`（保留 `api.snapshot_to_dict`），验证：`python manage.py check` 零问题
- [x] 4.3 删除 `apps/device_inspector/api.py` 的 `get_snapshot` 及其 `__all__` 条目，验证：`ruff check` / `ruff format --check` 通过，`pytest tests/graybox tests/api -q` 559 passed
- [x] 4.4 同步接口文档 `API-设备检查器`：端点全集改 6 个、删除「快照详情接口」概览行与章节、章节重排为 1–9 并修正「第 9 节」交叉引用，验证：文档内无详情端点章节，检索只剩分层 / 保存 / 删除三处出口
- [x] 4.5 同步 `tests/AGENTS.md` 模块映射表中设备检查器的覆盖描述，验证：描述与 `case/inspector.yaml` 的 10 条用例一致
- [x] 4.6 同步 PRD-03：删除详情接口小节、移除详情场景与用例表两行、更新「已知问题」第 9 条为已解决、修正对照口径与覆盖资产数字，验证：PRD-03 内不再有把该端点当作在册能力的表述

## 5. 门禁与归档

- [x] 5.1 后端门禁：`python manage.py check`（0 issues）、`makemigrations --check --dry-run`（No changes detected）、`ruff check`（All checks passed）、`ruff format --check`（7 files already formatted）
- [x] 5.2 测试门禁：`python -m pytest tests/graybox tests/api -q` → **559 passed**
- [x] 5.3 前端门禁：`npx vitest run` → **61 files / 350 tests passed**；`npx vue-tsc --noEmit` 无输出（仅既有 `ProjectTree.vue` 3 处）；`npm run build` 成功
- [x] 5.4 规范门禁：`npx openspec validate harden-inspector-frontend-and-retire-detail-api --type change --strict` valid；`npx openspec validate --specs --strict` 65 passed / 0 failed
- [x] 5.5 归档：`npx openspec archive harden-inspector-frontend-and-retire-detail-api -y` → 2026-09-23-harden-inspector-frontend-and-retire-detail-api
