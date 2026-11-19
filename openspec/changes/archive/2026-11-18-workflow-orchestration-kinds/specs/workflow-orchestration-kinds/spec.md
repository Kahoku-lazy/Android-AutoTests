## Purpose

把工作流拆成可组合的编排与种类：编排决定谁按什么循环协作，种类决定输入、资源和产物。一次运行只使用一对已实现的组合。

## ADDED Requirements

### Requirement: 工作流由编排与种类组成

系统 SHALL 把一条工作流记录为一种编排加一种种类。编排 MUST 只取 `sop`、`goal`、`team`。种类 MUST 只取 `ui_automation`、`case_authoring`、`requirement_breakdown`。系统 MUST 只允许 `sop + ui_automation`、`goal + case_authoring`、`team + requirement_breakdown` 三对。其它组合 MUST 在创建或编辑时拒绝，并且 MUST NOT 留下部分写入的记录。

#### Scenario: 允许的三对可以创建

- **WHEN** 用户分别提交上述三对中的任意一对，且该对要求的绑定都合法
- **THEN** 系统创建对应工作流

#### Scenario: 不允许的组合被拒绝

- **WHEN** 用户提交 `sop + case_authoring`、`goal + ui_automation` 或 `team + ui_automation`
- **THEN** 系统拒绝创建，并说明该组合不可用

### Requirement: 绑定形状由编排决定

`sop` 与 `goal` 的绑定 MUST 是一张执行名片加一张验收名片，两张可以相同。`team` 的绑定 MUST 是一张队长名片加至少两张成员名片，并且 MUST NOT 含验收名片。成员名片 MUST 互不相同，也 MUST NOT 与队长相同。每名成员 MUST 带一段非空说明，写明擅长什么以及交回什么。所有编号 MUST 指向现存助手名片。系统 MUST NOT 把名片的显示名、提示词、模型参数或工具勾选复制进工作流记录。

#### Scenario: Team 缺少成员说明

- **WHEN** 用户创建需求拆解工作流，但某名成员没有说明
- **THEN** 系统拒绝创建

#### Scenario: Team 不能带验收者

- **WHEN** 用户以 Team 编排提交执行者与验收者两张名片
- **THEN** 系统拒绝创建

### Requirement: 运行时现读名片并按种类收紧工具

系统 SHALL 在每次启动时读取绑定名片当时的提示词、模型参数与工具勾选。名片或其所引用的 Agent 配置不存在时，运行 MUST 失败，并且 MUST NOT 产生步骤、用例或模块。种类 MUST 再限制可用工具：UI 自动化只用设备工具，用例编写只用用例库工具，需求拆解只用只读的文档与检索工具。名片上超出该种类的工具 MUST NOT 挂到本次角色。未知工具名 MUST 使运行失败，并且 MUST NOT 开始工作。

#### Scenario: 改名片后下次运行使用新提示词

- **WHEN** 用户修改某工作流所绑定名片的系统提示词，再启动该工作流
- **THEN** 本次运行使用修改后的提示词

#### Scenario: 越权工具不进入本次运行

- **WHEN** 用例编写名片同时勾选了用例库工具和设备写操作工具
- **THEN** 本次用例编写角色只挂载用例库工具

### Requirement: 三段产物人工交接

需求拆解的成功产物 MUST 是模块清单，每项 MUST 含模块名、边界、测试点与不覆盖范围，并且 MUST NOT 含具体用例步骤。用例编写 MUST 以一个已确认模块的材料为输入，产物 MUST 进入用例库。UI 自动化 MUST 继续从平台用例或里程碑 YAML 取得输入。系统 MUST NOT 在任一段成功后自动创建下一段任务。

#### Scenario: 拆解成功不创建后续任务

- **WHEN** 一次需求拆解成功并形成两个模块
- **THEN** 任务结果含这两个模块的边界与测试点
- **AND** 系统不创建用例编写任务

#### Scenario: 拆解结果不能当作用例

- **WHEN** 用户查看一次成功的需求拆解结果
- **THEN** 结果中没有可直接执行的用例步骤

### Requirement: 启动时冻结组合

系统 SHALL 在创建任务时把工作流编号、编排与种类写入该任务自己的字段。此后编辑或删除工作流 MUST NOT 改变该任务已冻结的这三个值。任务列表与报告 MUST 使用冻结值，MUST NOT 回读工作流当前配置来改写历史行。

#### Scenario: 改工作流不影响已创建任务

- **WHEN** 一条任务已经创建，用户随后修改该工作流的名称或绑定
- **THEN** 该任务仍显示创建时冻结的编排与种类
