## Why

设备检查器前端功能分析给出的下一批动作有四项，都指向同一类问题：**口径没有唯一登记处、关键交互没有测试守护、已退役功能的残留仍在册**。
截图几何所在的 `ScreenshotView.vue`（474 行）与保存弹窗 `SaveToElementsDialog.vue`（174 行）零单测；`/media/` 路径拼接有 3 份实现、执行引擎占用前缀有 2 份；快照详情端点在「已保存页面」下线后已无任何调用方，却仍留在路由表、接口文档与接口用例中。

## What Changes

- **收敛共享登记处**：新增 `frontend/src/shared/helpers/mediaUrl.ts`（相对路径 → `/media/{path}`，空路径 → 空串）与 `frontend/src/shared/helpers/deviceOccupancy.ts`（占用前缀清单 + 前缀判定 + 执行引擎占用判定）。设备检查器、元素定位、AI 助手与设备管理四处改为复用，删除各自副本。
- **截图几何抽纯函数并补测**：把框归一化与命中策略（取包含命中点且面积最小的元素）抽到模块 `helpers/screenshotGeometry.ts`，组件只保留 DOM 基准换算；新增单测覆盖三种坐标形态、非法输入与命中取舍。
- **保存弹窗补用例**：新增 `SaveToElementsDialog` 的 P0 用例，覆盖目录级联来源（只含目录 / 末层目录的页面列表）、已有页面与新建页面两条提交分支、校验不通过不提交。
- **退役快照详情端点（**BREAKING**）**：删除 `GET /api/inspector/snapshots/{id}/` 的路由、视图、公开 API 函数与白名单条目；同步接口文档、接口用例与 PRD-03；快照回看一律经分层端点。
- **清理过期注释**：`ScreenshotView.vue` 中仍以「已保存页面」解释尺寸兜底的注释随该功能下线一并修正。

## 关联文档

- PRD-03

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `device-inspector-page`: 「请求失败如实呈现原因」的可重试来源不再包含已退役的快照详情；新增「检查器前端跨模块口径集中登记」（媒体展示 URL 拼接与执行引擎占用判定）。
- `device-inspector-snapshots`: 新增「快照详情端点退役，回看一律经分层端点」及其文档 / 用例同步要求。

## Impact

- 前端：新增 `frontend/src/shared/helpers/{mediaUrl.ts,deviceOccupancy.ts}`；改 `modules/device-inspector/store.ts`、`modules/device-inspector/components/{ScreenshotView.vue,StructureAnalysisPanel.vue}`、新增 `modules/device-inspector/helpers/screenshotGeometry.ts`；改 `modules/device-pool/constants.ts` 与 `components/{DeviceCard.vue,DeviceActionsCell.vue,DeviceStatusCell.vue}`；改 `modules/element-locator/helpers/elementPresentation.ts`、`modules/ai-assistant/helpers/task-detail.ts`。
- 后端：`apps/device_inspector/{urls.py,views.py,api.py}`（删路由、视图、`get_snapshot` 与白名单条目；`snapshot_to_dict` 保留——`capture_snapshot` 仍在用）。
- 测试：`tests/api/case/inspector.yaml` 删 TC-INS-003 / TC-INS-030（不删会让 `tests/graybox/unit/test_api_path_callers.py` 的 resolve 断言失败）；新增 `frontend/tests/device-inspector/p0/{screenshotGeometry.spec.ts,SaveToElementsDialog.spec.ts}`、`frontend/tests/shared/p0/{mediaUrl.spec.ts,deviceOccupancy.spec.ts}`。
- 文档：接口文档 `API-设备检查器`（概览表与端点章节）、`tests/AGENTS.md` 模块映射表（去掉「详情 / 页面回看」）、PRD-03（详情接口小节、用例表两行、已知问题第 9 条）。
- 兼容性：**BREAKING** 仅一处——`GET /api/inspector/snapshots/{id}/` 不再存在；仓内已无调用方，同一数据由分层端点覆盖。
