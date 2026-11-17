## Context

见 proposal.md - Why。仪表盘统计在 `DashboardStatsAPIView` 一次聚合。旧智能体装载已固定返回空列表，运行中任务在视图里写死为 0。任务清单与活动流仍按全表任务计，结果行仍指向已下线的 `/tasks/:id`。运营身份已有单一判定 `backend.shared.users.is_operator`，超级管理员天然算运营。

## Goals / Non-Goals

**Goals:**

- 平台概览的计数与点击目标，和平台助手页、任务清单、运营三页的真实数据源对齐。
- 运营三项计数在服务端按身份裁剪，普通用户响应里没有这个字段。
- 计数保持只读，且不把助手头像等大字段读进内存。

**Non-Goals:**

- 不改 AI 用量账单、账本、汇率与图表取数。
- 不改在线设备的全库口径，也不改用例项目卡。
- 不恢复 `/tasks/:id`，不新增写接口，不新增数据表。

## Decisions

1. **任务范围只计 `assistant_sop`。** 任务数量、运行中、排队、近 7 日柱、结果面板、最近动态共用这一个过滤。备选是继续计全表；那会把已退役的设备执行和用例编写算进平台概览，和任务清单对不上。

2. **运行中与排队一次聚合。** 对工作流任务按状态 `GROUP BY`，取出 `running` 与 `pending`。主数字用 `running`，副标题固定写「排队 N」，N 为 0 也返回。备选是两次 `COUNT`；结果相同，但每次刷新多一条查询。

3. **助手与工作流只做 `COUNT`。** 分别计 `ai_assistants` 与 `ai_sop_workflows`。不调用会把名片整行（含压缩头像）载入的列表函数。

4. **运营字段按身份附加。** 身份只读 `request.user_id`，用 `is_operator` 判定。为真时响应增加 `ops: {users, agents, models}`；为假时响应不含 `ops` 键。三项分别 `COUNT` 账号、`ai_roles`、`ai_model_configs`。备选是始终返回再用前端隐藏；普通用户直接打接口就能看到运营数字，不采用。

5. **活动流只留任务源。** 删除智能体更新分支，窗口仍是 100 条，分页参数不变。前端对未知 `type` 保持默认识别，不依赖 `agent` 类型继续渲染。

6. **结果行统一去任务清单。** `recent_tasks` 仍带 id，供行键使用；点击不再拼接 `/tasks/:id`，固定进入 `/tasks`。中断映射为 `interrupted`，取消映射为 `cancelled`，面板补这两档文案，不再落入「未执行」。

7. **前端不另拉运营接口。** 三张卡的数字只来自本次统计响应。运营页跳转沿用现有路由守卫，仪表盘不重复做授权。

## 模块防火墙自检

- `dashboard` 只读 `ai_assistant` 的 `AIAssistant`、`AISopWorkflow`、`AIRole`、`AIModelConfig`，以及 `task_list` 的 `Task`。不 import 对方的 service、views 或 runner。
- 账号计数只读 Django 用户 Model，不 import `ops_console` 或 `accounts` 的写接口。
- 本变更没有 INSERT / UPDATE / DELETE。
- 身份判定复用 `backend.shared.users.is_operator`，不在 dashboard 另写用户组判断。
- 前端只请求既有 `GET /api/dashboard/stats/` 与 `GET /api/dashboard/activities/`，不直连数据库，也不为三张运营卡另打 `/api/ops/*`。

## Risks / Trade-offs

- [普通用户看到的任务数包含他人的工作流任务] → 与当前任务清单「已登录即看全部工作流任务」保持一致；本次不新开按创建者过滤。
- [在线设备仍是全库，设备页会藏锁定 Wi-Fi] → 已确认平台概览计平台数；不在本次改设备可见性。
- [活动历史里不再出现智能体更新] → 旧智能体已下线，保留只会让活动流停在空源；回退时恢复该分支即可。

## Migration Plan

1. 先后端：统计响应先给出新计数字段，活动流先去掉智能体更新。
2. 再前端：按新字段渲染卡片与结果行；旧响应缺字段时按 0 与空列表降级，避免发布窗口白屏。
3. 回退：前端先回到旧卡片，后端再去掉 `ops` 与新计数字段。无迁移、无数据改写。

## Open Questions

无。卡片口径、排队副标题、运营可见范围已在本轮确认。
