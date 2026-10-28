# 设计：任务报告瘦身与首屏提速

## 背景

任务 142 实测（2026-10-23，本机）：事件 174,098 行、报告响应 9.47MB / 4.4s、`rounds` 5.04MB 与 `cases[].rounds` 5.06MB 内容重复、前端 60,187 个 DOM 节点、首屏 12.8s。前三项都能在不动数据模型的前提下收掉。

## 决策

### D1：`round_id` = 轮次在 `data.rounds` 中的下标

`build_task_flow` 已经按执行顺序产出 `rounds`，用数组下标做 `round_id` 最省事且稳定（同一请求内唯一）。`data.cases[].rounds` 改成 `round_ids`，由 `_flow_cases` 把「该用例的轮次下标」收集起来。前端不需要再按字段猜归属。

不选「给轮次加数据库 id」：轮次不是表，加 id 需要额外映射，且跨请求稳定性没有需求。

### D2：终态报告缓存放 Django 默认缓存，键带最大事件 seq

`CACHES` 未配置，默认 LocMem。测试与 CI 没有 Redis（`tests/test_settings.py` 用内存 channel layer，CI 无 redis 服务），因此不引入 Redis 缓存后端，避免测试与 CI 依赖。

- 键：`task-flow:{task_id}:{max_seq}`；`max_seq` 来自 `TaskEvent.objects.filter(task_id=...).aggregate(Max("seq"))`，走 `idx_evt_task_seq` 索引，毫秒级。
- 只缓存终态（`completed` / `failed` / `interrupted` / `cancelled` / `stopped`）；`running` / `pending` 直接走实时构建。
- TTL 600s。重跑会写入更大 `seq`，键随之前移，旧报告自然失效。
- 已知限制：多进程部署时每个 worker 各有一份缓存，命中率取决于负载均衡；后续把 `CACHES` 切到 Redis 即可，接口不变。

### D3：ETag 与 304 在视图层做

`payload` 序列化后取 `sha1` 作强 ETag；`If-None-Match` 相等返回 304，不带体。304 不经过序列化省略——`etag` 与缓存一起存，命中时不再 dumps。

`extend_schema` 补 304 响应，OpenAPI 基线重新生成。

### D4：前端默认展开第一个用例 + 每用例轮次分页 20

- `openCases` 初始化为 `new Set([0])`（仅当有用例时）。
- 每个用例一个页码状态（`reactive(new Map())` 或 `ref({})`），默认 1；`round_ids` 切片 `slice((page-1)*20, page*20)`。
- 用例卡加 `content-visibility: auto; contain-intrinsic-size: 600px;`，视口外的用例跳过布局/绘制。
- 展开时按 `round_ids` 从 `rounds` 建立 `Map<round_id, round>`，不做对象拷贝。

### D5：不动的东西

- 不删事件行、不改引擎写入、不动 `ToolCallDeltaEvent`（既有 spec 要求增量段仍以一条出现且 `count` 保留，删它收益只有约 0.4MB）。
- 不改 `detail` 字段完整展示的既有约束。
- 不改媒体接口与懒加载。

## 风险

- **BREAKING**：`data.cases[].rounds` 消失。仓内消费方只有 `TaskDetailPage.vue`，已一并改；无外部调用方。
- LocMem 缓存对多进程只是「每进程各一份」，本机开发（runserver 单进程）实测有效；生产需切 Redis，接口不变。
- `content-visibility` 在极老浏览器（Chrome < 85）不生效，退化为正常渲染，不影响正确性。
- 分页会改变用户看到的信息密度（一次只见 20 轮），已在 spec 中登记为可见行为变化。

## 验证

- 接口：首次 <1.5s、二次 <300ms、响应 <5MB、ETag 304。
- 前端：首屏可见 <2s、DOM <3,000、默认 1 个用例展开、翻页 20 条。
- 回归：`python -m pytest -c tests/pytest.ini tests/graybox/integration -q`；`npx vitest run tests/task-list`；`python run.py check`。
