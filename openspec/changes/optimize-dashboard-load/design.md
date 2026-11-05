## Context

现状与实测见 proposal.md - Why。关键约束：

- 页面在 `DashboardView.logic.ts` 与 `index.vue` 各注册了一次 `useDashboardAutoRefresh`，两个 5s `setInterval` 同时跑。
- `useDashboardAutoRefresh` 的注释写「每 30 秒」，常量却是 `5_000`。
- 仪表盘 5 个统计函数各自调用 `_agents()`；`AIAgent.avatar` 有一条 6.5MB base64。
- `usage_summary` 内部对每个分类再查一次厂商；仪表盘调它 5 次。
- 服务端是 Daphne + 同步 DRF 视图，并发排队时单请求会从 1.9s 涨到 4.9s（实测）。

## Goals / Non-Goals

**Goals:**

- 打开仪表盘 1–2 秒内出数；停留期间不再越来越慢。
- 接口响应结构与统计口径零变化。
- 用测试锁住「单轮询」「不叠加」「SQL 预算」三条，避免回退。

**Non-Goals:**

- 不改头像存储（6.5MB base64 落库）——影响面在 `ai_assistant`，另开变更。
- 不拆 stats 接口、不加缓存层、不做前端分片渲染。
- 不动图表视觉与页面版式。

## Decisions

**1. 轮询收口到编排层，并加在途守卫。**

`index.vue` 删除第二次 `useDashboardAutoRefresh`，只保留 `DashboardView.logic.ts` 里的那一处。间隔取 30s（与注释一致），`tick()` 用 `inFlight` 标记：上一轮未完成直接 return。备选「用 `setTimeout` 自调度」同样能防叠加，但改动面更大；守卫方案只加一个布尔。

**2. 静默刷新再守一层。**

`refreshSilently` 记录 `silentInFlight`，重复调用直接返回。轮询已防叠加，这里防的是「可见性回调 + 定时器」同一瞬间双触发。

**3. 智能体一次装载、按需取列。**

新增 `load_visible_agents(user_id)`：`filter_agents_for_user(AIAgent.objects.only(...), user_id)`，列只含 `id/name/status/owner_id/route_configs/updated_at/model_provider/model_name`。之所以用 `only` 而不是 `defer("avatar")`：`tags`、`description` 等长文本同样不该进内存；`only` 命中函数实际用到的字段，越界访问才会回查（现有函数不越界）。视图层调用一次，把列表传给五个统计函数与活动流，`agents` 计数也用 `len()` 而不是再查两次。

**4. 用量汇总改成「一次分组，内存拼装」。**

`usage_summary` 内部改为单条 `.values("category","provider").annotate(...)`，在 Python 里拼 total / categories / providers；仪表盘用 `usage_dashboard()` 批量产出五个口径（4 条分组查询 + 1 条 recent）。保留 `usage_summary` 原签名与输出，避免其它调用点（当前只有仪表盘）未来复用时口径不一致。

**5. 测试锁三条预算。**

- 前端：定时器只注册一个、慢请求期间不再发、间隔 ≥15s；
- 后端：用 `django_assert_num_queries` 断言统计接口 SQL ≤ 25；
- 一致性：新旧聚合在测试数据上输出一致。

## 模块防火墙自检

- 跨 App：`dashboard` 读 `usage_ledger` 只经其 `api.py`（`usage_dashboard`），未 import 内部实现；`ai_usage` 读 `ai_assistant` 仍走既有 `api.filter_agents_for_user`。
- 写库：本变更全为只读聚合，无 INSERT/UPDATE/DELETE。
- engines：不涉及。
- 前端：只改轮询与请求节流，不直连数据库。

## Risks / Trade-offs

- [`.only()` 漏列字段导致 N+1 回查] → 字段清单覆盖现有五个函数实际访问的列；测试断言 SQL 条数，漏列会立刻超标。
- [轮询从 5s 调到 30s，用量数字不再「跟手」] → 页面仍保留手动刷新与可见性补刷；30s 与文件原注释一致，若产品要求更实时再单开。
- [`usage_summary` 重写改变排序或精度] → 保留「按 tokens 降序」与 Decimal 精度；新增新旧一致性测试。
- [统计函数新增 `agents` 参数影响其它调用方] → 参数默认 `None`，缺省仍自行装载。

## Migration Plan

1. 后端先行（接口变快但结构不变）→ 前端随后（轮询去重与节流）。
2. 回滚：前端单文件回退即可；后端保留旧 `usage_summary` 签名，仪表盘改回 5 次调用也能工作。
3. 无 schema 变更、无数据迁移。
