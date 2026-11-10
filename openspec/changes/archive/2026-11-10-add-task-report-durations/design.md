## Context

耗时数据已经在库里：`TaskEvent` 每行都有 `started_at` / `ended_at` / `duration_ms`（`event_store._row()` 逐行写入）。报告构建 `_load_events()` 目前只取 6 个瘦列（`seq` / `event_type` / `is_delta` / `step_seq` / `attempt` / `delta_count`），第二次 `_load_details()` 只给「每段第一行」补展示列与 `duration_ms`。

分组口径（不能动）：`_rounds()` 按 `ReplyStartEvent` / `SOP_STEP_STARTED` 开新轮，`_split_round_groups()` 按 `step_seq` 倒退切用例，`_annotate()` 负责把私有键转成对外字段并剥离。动机见 proposal.md - Why。

## Goals / Non-Goals

**Goals:**

- 四层耗时随报告一次下发，前端只格式化。
- 零额外扫描次数、零表结构变更、零新接口。
- 口径写死在一处，避免前后端各算一套。

**Non-Goals:**

- 不做跨用例汇总、排行、趋势图。
- 不把耗时塞进每条事件项（载荷会随事件数膨胀）。
- 不改页头「执行 3分12秒」的中文写法。

## Decisions

**1. 起止时间只给「每段第一行」，不动瘦列扫描。**

`started_at` / `ended_at` 加进 `_DETAIL_COLUMNS`，只在给代表行补展示字段的那一次查询里取，而不是扩宽 `_SLIM_COLUMNS`。理由：报告只需要「每轮第一个事件的开始」和「每轮最后一个事件的结束」，代表行就是每次折叠段的起点，增量行不需要时间；扩宽瘦列会让 15 万事件任务多取 30 万个 datetime。聚合查询方案被否掉：`(step_seq, attempt)` 在多用例任务里会跨用例撞号，而 `case_title` 在存量事件里可能为空。

**2. 轮级用纯模型时长，步骤/用例用墙钟。**

一轮执行里既有模型调用，也有设备点击与串口取证，墙钟当"模型耗时"会虚高；而用户对"这一步花了多久"的直觉就是墙钟。两种口径必须靠措辞区分（`模型 38s` vs `3m12s`），否则读者会误以为 `执行 + 验收 = 步骤`。

**3. 每轮的起止在 `_rounds()` 里就地累加。**

`_rounds()` 已经在遍历每一轮的事件项，顺手维护 `_start` / `_end` / `_model_ms` 三个私有键，`_annotate()` 再把它们转成 `model_ms` / `running` 并剥离——与既有 `_kind` / `_attempt` 的处理方式一致，不新增一次遍历。步骤与用例的跨度在 `_flow_cases()` 里用同一批 `_start` / `_end` 求 min/max，保证三层自洽。

**4. `running` 由「缺少 `ended_at`」推导，不由任务状态推导。**

轮次是否结束看该轮事件的 `ended_at`，而不是看 `task.status`：一个任务可能已经 `completed`，但某轮因为异常没写结束事件。任务状态只决定页头，不决定轮次。

**5. 缺失时间戳时给 0 并让前端不渲染。**

存量事件（老版本埋点）可能 `started_at` 为空。此时不拿 `called_at` / `moment` 推算——推算出来的数字会被当成真实耗时。约定 `0` 或 `null` 表示"无数据"，前端按"缺失不显示"处理。

**6. 前端只在 helpers 里加一个纯函数。**

`formatDurationMs(ms)` 放在 `helpers/report-steps.ts`，三处模板共用。分组、求和、回退一律在后端，前端不重算（模块红线：只读展示，不重排）。

## 模块防火墙自检

- 跨 App import：无新增。只改 `backend/apps/task_list/task_reports.py` 内部函数与前端展示层。
- `INSERT/UPDATE/DELETE`：无。纯只读聚合，不写库。
- 前端不直连数据库：遵守，字段仍来自既有 `GET /api/tasks/{id}/report/`。
- 通道：不新增 HTTP 端点、不新增 WebSocket / SSE。
- 模块边界：`task-list` 内部改动，`shared/types/ai.ts` 只补字段类型，不引入跨模块依赖。

## Risks / Trade-offs

- **15 万事件任务的性能预算** → 瘦列扫描（`_SLIM_COLUMNS`）与分组口径都没变，只在原本就存在的「代表行明细」查询里多取 2 列，行数等于折叠段数（远小于事件总数）；已用真实任务（1,048 事件）与既有报告用例回归，未出现退化。
- **折叠增量轮的结束时间取的是代表行 `ended_at`** → 该行的 `duration_ms` 已覆盖整段流式时长，取 `max(ended_at, started_at + duration_ms)` 兜住流式尾巴，误差在百毫秒级，对秒级展示无影响。
- **`model_ms` 回退为墙钟会掩盖"没有模型事件"** → 回退只在该轮完全没有 `ModelCallEndEvent` 时发生，且前端仍按「模型 xx」展示；事件齐全时不触发。
- **多用例任务里步骤号重复** → 跨度按「用例内轮次」求，不用 `(step_seq, attempt)` 做全局键，避免跨用例串号。

## Migration Plan

纯增量字段，无迁移、无部署顺序要求。

- 上线：后端先发（多出字段不影响老前端），前端随构建更新即可。
- 回滚：前端回退后新字段被忽略；后端回退后前端按「缺失不显示」处理，不会报错。
