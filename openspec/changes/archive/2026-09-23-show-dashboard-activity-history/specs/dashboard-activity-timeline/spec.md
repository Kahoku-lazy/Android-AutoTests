## Purpose

定义仪表盘「最近活动」主屏十条可视槽与历史弹层：用户能在固定高度内扫最近十条，并通过按键分页查看更早的只读活动。

## ADDED Requirements

### Requirement: Recent activity board reserves ten item slots

仪表盘「趋势与动态」章节内的最近活动列表区 MUST 预留恰好十条活动信息的可视高度。条目不足十条时 MUST 仍保持该高度（空白槽可见），MUST NOT 随条目变少而塌缩。主屏 MUST 最多渲染最新十条；若返回超过十条，超出部分 MUST 仅能通过历史入口查看，MUST NOT 把主屏撑成无上限列表。

#### Scenario: Empty board still occupies ten slots

- **WHEN** 用户打开仪表盘且活动接口返回空数组
- **THEN** 最近活动列表区的可视高度仍等于十条槽位
- **AND** 区内展示「暂无活动记录」（或语义等价空态文案）

#### Scenario: Fewer than ten items keep the reserved height

- **WHEN** 活动接口返回 3 条记录
- **THEN** 主屏渲染这 3 条
- **AND** 列表区可视高度仍等于十条槽位

#### Scenario: Board never shows more than ten items

- **WHEN** 活动接口在默认查询下返回 10 条
- **THEN** 主屏恰好展示这 10 条且无需滚动即可看到全部十条标题行
- **AND** 不出现第 11 条

### Requirement: History control opens a paged activity dialog

最近活动标题行 MUST 提供「查看历史」按键。激活后 MUST 打开本页弹层（MUST NOT 新增路由或侧栏入口）。弹层 MUST 从同一活动接口拉取默认十条之后的记录（或首屏之后的分页），并允许继续向后翻页直到该窗口内没有更多条目。关闭弹层 MUST 回到仪表盘且不改变主屏已展示的十条。

#### Scenario: Open history from the timeline header

- **WHEN** 用户在最近活动标题行激活「查看历史」
- **THEN** 出现标题为「活动历史」（或语义等价）的弹层
- **AND** 浏览器地址仍为 `/dashboard`

#### Scenario: History lists older items beyond the board

- **WHEN** 合并后的活动窗口超过 10 条且用户打开历史弹层
- **THEN** 弹层列出第 11 条及之后的记录（按时间倒序）
- **AND** 主屏十条保持不变

#### Scenario: History empty when nothing older exists

- **WHEN** 合并窗口不超过 10 条且用户打开历史弹层
- **THEN** 弹层展示空态，说明没有更多历史记录

### Requirement: Activities endpoint stays read-only with offset pagination

`GET /api/dashboard/activities/` MUST 保持登录可读、信封 `{status, data}` 且 `data` 为活动对象数组（非对象包裹）。未传查询参数时 MUST 返回时间倒序的最新至多 10 条。查询参数 `limit` 与 `offset` SHALL 为非负整数：`limit` 缺省 10、最大 50；`offset` 缺省 0。非法值 MUST 以 HTTP 400 返回明确 `message`，MUST NOT 静默改写成默认值。系统 MUST NOT 提供写方法。

#### Scenario: Default query matches the board page

- **WHEN** 已登录用户请求 `GET /api/dashboard/activities/` 且不带查询参数
- **THEN** HTTP 200 且 `data` 为数组，长度不超过 10
- **AND** 条目按 `time` 倒序

#### Scenario: Offset skips the board page

- **WHEN** 已登录用户请求 `GET /api/dashboard/activities/?offset=10&limit=50`
- **THEN** HTTP 200 且 `data` 为数组
- **AND** 其中条目不与默认请求的前 10 条重复（窗口内不足 10 条时数组可更短或为空）

#### Scenario: Invalid limit is rejected

- **WHEN** 已登录用户请求 `GET /api/dashboard/activities/?limit=0` 或 `limit=51` 或非整数 `limit`
- **THEN** HTTP 400 且响应含明确 `message`

### Requirement: Activity feed merges assistant tasks and agent updates

活动条目 MUST 由当前用户可见的助手任务卡（`type` 为 `run`）与智能体更新（`type` 为 `agent`）合并、按 `time` 倒序构成。系统 MUST NOT 再查询已删除的测试执行表。合并窗口上限 MUST 为 100 条（先各源截取再合并截断），分页在该窗口内切片。每条 MUST 含 `type`、`action`、`time`（`YYYY-MM-DD HH:MM`）；`detail` MAY 省略。

#### Scenario: Task card appears as a run activity

- **WHEN** 当前用户可见智能体下存在助手任务卡
- **THEN** 活动数组中出现 `type` 为 `run` 的条目
- **AND** `action` 含该任务标题（无标题则用目标或「未命名任务」）

#### Scenario: Agent update remains an agent activity

- **WHEN** 当前用户可见智能体发生更新
- **THEN** 活动数组中出现 `type` 为 `agent` 的条目
- **AND** `action` 含该智能体名称
