# dashboard-load-performance Specification

## Purpose
约束仪表盘的加载预算：一个页面只允许一个轮询、慢请求不得叠加、统计接口不重复读取大字段，用量汇总一次聚合算完，保证打开页面能在一两秒内出数而不是十几秒。

## Requirements

### Requirement: 仪表盘只挂一个轮询且请求不叠加

仪表盘页面 MUST 只注册一个静默轮询定时器；轮询间隔 MUST NOT 小于 15 秒。上一轮刷新尚未返回时，下一次触发 MUST 被跳过，MUST NOT 并发发出新的统计数据请求。页面隐藏时 MUST 暂停轮询，回到可见时 SHALL 立即补一次。

#### Scenario: 页面只挂一个定时器

- **WHEN** 用户打开仪表盘并停留
- **THEN** 每个轮询周期只发出一次统计数据请求与一次活动请求
- **AND** 不出现两个定时器各发一遍、请求量翻倍的情况

#### Scenario: 慢请求不叠加

- **WHEN** 上一次静默刷新尚未返回，下一次轮询触发
- **THEN** 本轮被跳过，不发起新请求
- **AND** 上一次返回后按正常节奏继续

#### Scenario: 隐藏暂停、回来自动补

- **WHEN** 页面切到后台超过一个周期后切回
- **THEN** 后台期间不轮询
- **AND** 回到可见时立即补一次

### Requirement: 统计接口只读一次智能体且不取头像

`GET /api/dashboard/stats/` 与 `GET /api/dashboard/activities/` MUST 在一次请求内只加载一次当前用户可见的智能体列表，MUST NOT 读取 `avatar` 大字段；单次统计请求的 SQL 条数 MUST NOT 超过 25 条。响应字段、统计口径与排序 MUST 保持不变。

#### Scenario: 一次请求只查一次智能体

- **WHEN** 客户端请求仪表盘统计
- **THEN** 该请求对 `ai_agents` 的查询恰好一次
- **AND** 查询列中不包含 `avatar`

#### Scenario: 查询预算

- **WHEN** 在当前数据规模（约 20 个任务、4 千条用量记录）下请求统计接口
- **THEN** 单次请求 SQL 条数不超过 25 条
- **AND** 进程内耗时不超过 1.5 秒

#### Scenario: 响应结构不变

- **WHEN** 对比改动前后的统计响应
- **THEN** 顶层字段（devices / cases / agents / ai_usage / usage_ledger / charts / execution_summary / recent_tasks / …）完全一致
- **AND** `usage_ledger` 的 today / total / voice_today / voice_total / recent 结构与数值口径一致

### Requirement: 用量汇总单次聚合

用量汇总 MUST 通过一次按 `category` + `provider` 的分组聚合完成，MUST NOT 为每个分类再单独查询厂商；同一周期与来源 MUST NOT 重复执行相同聚合。今日、累计、语音今日、语音累计与最近明细 SHALL 由一次批量调用产出。

#### Scenario: 分类数量不影响查询数

- **WHEN** 用量记录按分类与厂商分组统计
- **THEN** 查询数与分类数量无关
- **AND** 不再出现「每个分类一次厂商聚合」的 N+1

#### Scenario: 输出与旧口径一致

- **WHEN** 用同一批数据比较新旧汇总结果
- **THEN** total、categories、providers 的 tokens / cost / calls 数值一致
- **AND** 分类与厂商的排序仍按 token 降序

#### Scenario: 批量产出五个口径

- **WHEN** 仪表盘请求用量汇总
- **THEN** 一次调用返回 today / total / voice_today / voice_total / recent
- **AND** 用量相关查询不超过 6 条
