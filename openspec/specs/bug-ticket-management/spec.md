# bug-ticket-management Specification

## Purpose
把任务清单里的执行错误集中成可追溯、可分类、可处理的 BUG 台账：UI 自动化失败与测试用例编写问题分开登记，每张 BUG 单都保留来源任务编号，并能从 BUG 单回到任务详情。

## Requirements

### Requirement: BUG 单分类与任务关联

系统 SHALL 为每张 BUG 单持久化分类、标题、错误正文、处理状态、来源任务编号、任务标题快照、任务类型、Agent 编号与创建人。分类 MUST 只有 `ui_automation`（UI 自动化）与 `case_authoring`（测试用例编写）两种，并 MUST 由来源任务的 `task_kind` 映射：`device_control` → `ui_automation`，`case_authoring` → `case_authoring`。每张 BUG 单 MUST 带非空 `task_id`，并 MUST 提供稳定的 BUG 编号用于展示。

#### Scenario: UI 自动化任务生成 UI 自动化 BUG
- **WHEN** 一个 `task_kind=device_control` 的任务进入失败终态
- **THEN** 生成的 BUG 单分类为 `ui_automation`
- **AND** BUG 单的 `task_id` 等于该任务编号，任务标题快照等于该任务标题

#### Scenario: 用例编写任务生成用例编写问题
- **WHEN** 一个 `task_kind=case_authoring` 的任务验收未通过
- **THEN** 生成的 BUG 单分类为 `case_authoring`
- **AND** BUG 单的 `task_id` 等于该任务编号

#### Scenario: BUG 编号稳定且可读
- **WHEN** 用户打开 BUG 单列表或详情
- **THEN** 每张 BUG 单显示形如 `BUG-0001` 的编号
- **AND** 同一张 BUG 单在列表、详情与刷新后编号不变

### Requirement: 任务错误自动登记为 BUG 单

系统 SHALL 在任务终态落库后自动登记 BUG 单。UI 自动化任务状态为 `failed` 时 MUST 按 `Task.result.failed` 中的每个失败用例各登记一张 BUG 单；`failed` 列表为空时 MUST 登记一张任务级 BUG 单；状态为 `interrupted` 时 MUST 登记一张任务级 BUG 单。用例编写任务状态为 `failed` 时 MUST 登记一张任务级 BUG 单；任务为 `completed` 但 `Task.result.case_import.status=failed` 时 MUST 登记一张入库失败 BUG 单。`cancelled` 任务 MUST NOT 登记。登记失败 MUST NOT 改变任务状态、任务结果或验收结论。

#### Scenario: 多个失败用例逐条登记
- **WHEN** UI 自动化任务失败，且 `result.failed` 包含两个用例标题
- **THEN** BUG 台账新增两张 `ui_automation` BUG 单，分别对应用例标题
- **AND** 两张 BUG 单都关联同一个任务编号

#### Scenario: 没有失败用例明细时登记任务级 BUG
- **WHEN** UI 自动化任务进入 `failed` 且 `result.failed` 为空
- **THEN** 新增一张任务级 `ui_automation` BUG 单，正文包含任务结果中的原因

#### Scenario: 中断任务登记
- **WHEN** 任务因服务重启被标记为 `interrupted`
- **THEN** 新增一张对应分类的 BUG 单，正文说明任务中断

#### Scenario: 用例入库失败登记
- **WHEN** 用例编写任务为 `completed` 且 `case_import.status=failed`
- **THEN** 新增一张 `case_authoring` BUG 单，正文包含入库失败原因
- **AND** 任务仍保持 `completed`，验收结论不变

#### Scenario: 取消任务不登记
- **WHEN** 任务被用户取消并进入 `cancelled`
- **THEN** BUG 台账不新增该任务的 BUG 单

### Requirement: BUG 登记幂等且尊重处理状态

同一任务、同一分类、同一来源键的 BUG 单 MUST 唯一。重复执行自动登记或历史同步 MUST NOT 新增重复记录；已存在的 BUG 单 MAY 更新标题、正文与任务快照，但 MUST NOT 覆盖用户已设置的处理状态 `open` / `resolved` / `ignored`。处理状态为 `resolved` 时 MUST 记录解决时间；状态回退为非 `resolved` 时 MUST 清空解决时间。

#### Scenario: 重复同步不翻倍
- **WHEN** 对同一批失败任务连续执行两次历史同步
- **THEN** 第二次不新增任何 BUG 单
- **AND** 第二次返回的 `created` 计数为 0

#### Scenario: 已解决状态不被同步覆盖
- **WHEN** 用户把一张 BUG 单改为 `resolved` 后再次同步来源任务
- **THEN** 该 BUG 单仍为 `resolved`
- **AND** 解决时间保持不变

#### Scenario: 重新打开清空解决时间
- **WHEN** 用户把一张已解决 BUG 单改回 `open`
- **THEN** 状态变为 `open`
- **AND** 解决时间被清空

### Requirement: BUG 单查询、详情与处理

系统 SHALL 提供 BUG 单列表、详情与处理状态更新能力。列表 MUST 支持按分类、处理状态与关键字过滤，关键字 MUST 匹配 BUG 标题、错误正文、任务标题与任务编号；列表 MUST 返回总数、分类计数、待处理计数与当前过滤结果。详情 MUST 返回完整错误正文与来源任务信息。列表与详情 MUST 只包含当前用户可见 Agent 产生的 BUG 单，MUST NOT 跨用户泄露。处理状态 MUST 只允许 `open`、`resolved`、`ignored`。

#### Scenario: 按分类查看
- **WHEN** 用户选择「UI 自动化」分类
- **THEN** 列表只返回 `ui_automation` BUG 单
- **AND** 选择「测试用例编写」时只返回 `case_authoring` BUG 单

#### Scenario: 按任务编号检索
- **WHEN** 用户在关键字框输入任务编号
- **THEN** 列表返回来源任务编号匹配的 BUG 单

#### Scenario: 非法状态被拒绝
- **WHEN** 客户端把 BUG 单状态改为 `open` / `resolved` / `ignored` 之外的值
- **THEN** 接口返回 400，BUG 单状态保持不变

#### Scenario: 不可见 Agent 的 BUG 不出现
- **WHEN** 当前用户看不到某个 Agent
- **THEN** 该 Agent 任务产生的 BUG 单不出现在列表、统计与详情中

### Requirement: 历史任务错误可补录

系统 SHALL 提供历史同步能力，扫描当前用户可见任务中处于 `failed` / `interrupted` 的任务，以及 `completed` 但用例入库失败的任务，按自动登记规则补录 BUG 单。同步 MUST 幂等，并 MUST 返回扫描数、新增数、更新数与跳过数。

#### Scenario: 同步历史失败任务
- **WHEN** 用户点击「同步历史错误」且存在历史失败任务
- **THEN** 这些任务按分类与失败用例补录为 BUG 单
- **AND** 响应包含扫描数、新增数与更新数

#### Scenario: 没有历史错误
- **WHEN** 当前用户可见任务中没有可登记的错误
- **THEN** 同步成功返回，新增数为 0，不创建空 BUG 单
