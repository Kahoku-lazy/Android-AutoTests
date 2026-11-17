## ADDED Requirements

### Requirement: Task card names the SOP kind

任务清单页的任务卡 MUST 按任务类型显示三类文案：设备执行、用例编写、SOP。类型为 `assistant_sop` 时 MUST 显示「SOP」，MUST NOT 显示成设备执行。其它类型的既有文案 MUST 保持不变。

#### Scenario: SOP 任务显示 SOP

- **WHEN** 用户在任务清单查看一条 `assistant_sop` 任务
- **THEN** 该卡类型文案为「SOP」

#### Scenario: 设备任务不被改名

- **WHEN** 用户查看一条设备执行任务
- **THEN** 该卡类型文案仍为「设备执行」

### Requirement: SOP submit success offers a task list link

从工作流提交一条 SOP 任务成功后，系统 MUST 留在当前页，并在成功提示中提供进入 `/tasks` 的链接。系统 MUST NOT 因提交成功而自动离开当前页。提交字段与提交接口 MUST 保持不变。

#### Scenario: 成功后只给链接

- **WHEN** 用户在工作流任务弹窗提交成功
- **THEN** 当前页仍是助手页，成功提示含可进入任务清单的链接

#### Scenario: 不自动跳转

- **WHEN** 提交成功且用户没有点击该链接
- **THEN** 路由不进入 `/tasks`
