## Why

真机实测（快照 #350 / #348，pkg `com.govee.home`，全量节点 150 个）：分层响应里的分组计数是**全量**口径，元素条目却只有**前 100 条**。同一屏上「内容控件·文本 19」与表格「共 10 条」自相矛盾，被丢掉的 49 个元素在表格与圈选图上都不存在。

根因是条数参数带一个隐式上限，且调用方不传参数时它会静默生效：

- `apps/device_inspector/views.py:127`：`limit = int(request.query_params.get("limit", 100))`
- `apps/device_inspector/api.py:283`：`"elements": matched[offset : offset + limit]`
- `frontend/src/modules/device-inspector/store.ts:208` → `api.ts:14`：前端调用时不传任何参数

元素总数 ≤ 100 时一切正常 —— 这正是前置变更的真机验收（快照 #347，79 节点）没能暴露它的原因。同一响应内「摘要全量 + 条目切片」本身就是两处口径，本单让它们不可能再分叉。

## What Changes

- **条数参数缺省 = 不施加任何上限**：未指定 `limit` 时返回自 `offset` 起的全部命中，使同一响应内的分组计数与元素条目必然一致。
- **显式 `limit` 的语义不变**：指定条数时仍按「偏移 + 条数」返回区间，命中总数仍为筛减后的全量条数。
- **不谎报区间**：未施加上限时，响应中的条数字段为 `null`，MUST NOT 回填一个实际未生效的上限值。
- **前端无需改动**：前端本就不传参数，修好后自动拿到全量。

## 关联文档

- PRD-03（设备检查器）

## Capabilities

### Modified Capabilities

- `device-inspector-layers`: 新增「条数缺省时不施加隐式上限」要求，明确缺省不得截断，并规定未施加上限时响应区间的表示与「分组计数 = 返回条目数」的不变量。

## Impact

- 后端：`apps/device_inspector/api.py`（`list_layers` 的条数缺省语义）、`apps/device_inspector/views.py`（参数解析与校验）
- 前端：无改动（`api.ts` / `store.ts` 本就不传条数参数）
- 测试：`tests/graybox/integration/test_inspector_layers_api.py` 增补「缺省不截断」与「计数与条目一致」用例
- 文档：`dev_docs/DEV_TEST/接口文档/API-设备检查器.md` 的分层小节补条数缺省语义
- 不涉及：算法层、引擎层、快照落库口径、显式分页的既有行为
