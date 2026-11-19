## MODIFIED Requirements

### Requirement: Task list page hosts the task board

系统 SHALL 在 `/tasks` 提供「任务清单」页，页头标题 MUST 为「任务清单」。该页 MUST 用表格展示工作流任务记录，MUST 提供工作流分类与执行状态两个独立筛选。该页 MUST NOT 提供新建任务入口，MUST NOT 使用任务卡片或按状态分组的折叠列表。平台小助手页 MUST NOT 渲染任务清单。任务重跑、关闭与清空的接口契约 MUST 保持不变。

#### Scenario: 打开任务清单页

- **WHEN** 用户访问 `/tasks`
- **THEN** 页头显示「任务清单」
- **AND** 页面以表格展示工作流任务，并提供工作流分类与执行状态筛选
- **AND** 页面没有「新建任务」按钮

#### Scenario: 平台小助手不再承载任务卡片

- **WHEN** 用户打开平台小助手页
- **THEN** 页面不出现任务清单表格或「新建任务」入口

### Requirement: Task list card content and actions

任务清单表格的一行 MUST 展示任务编号、工作流、执行状态、设备、附件名、创建时间、耗时与费用。失败或已中断的行 MUST 提供「重新执行」，运行中的行 MUST 提供「关闭」，有报告的行 MUST 提供「报告」。行内 MUST NOT 展示目标全文，也 MUST NOT 提供进入 `/tasks/:id` 的详情入口。

#### Scenario: Card fields

- **WHEN** 用户查看任务清单中的一行
- **THEN** 行内可见编号、工作流、执行状态、设备、附件名、创建时间、耗时与费用
- **AND** 不展示目标全文

#### Scenario: Failed and running actions

- **WHEN** 行状态为失败、已中断或运行中
- **THEN** 失败或已中断的行可见「重新执行」
- **AND** 运行中的行可见「关闭」

#### Scenario: Detail navigation

- **WHEN** 用户点击一行的「报告」
- **THEN** 系统打开该任务已有的报告
- **AND** 不进入 `/tasks/:id`

### Requirement: Task card names the SOP kind

任务清单表格 MUST 只展示 `assistant_sop` 记录。设备执行与用例编写记录 MUST NOT 出现在该表格中。表格 MUST NOT 再把记录分成设备执行、用例编写、SOP 三类展示。

#### Scenario: SOP 任务显示 SOP

- **WHEN** 数据库同时存在工作流、设备执行和用例编写任务
- **THEN** 任务清单表格只出现工作流记录

#### Scenario: 设备任务不被改名

- **WHEN** 用户查看任务清单
- **THEN** 表格中没有「设备执行」或「用例编写」类型列

## ADDED Requirements

### Requirement: 工作流分类与执行状态分开筛选

任务清单 SHALL 用顶部分类标签筛选工作流，用独立下拉筛选执行状态。分类 MUST 包含「全部」，以及当前仍存在的工作流。已删除工作流 MUST NOT 出现在分类中，但其历史记录 MUST 仍可在「全部」中看到。执行状态选项 MUST 包含全部、待执行、执行中、任务成功、任务失败、已中断、任务取消。两个条件 MUST 同时生效。切换任一筛选 MUST 回到第一页。

#### Scenario: 按工作流分类

- **WHEN** 用户选择某个仍存在的工作流分类
- **THEN** 表格只显示该工作流的记录

#### Scenario: 分类后再按状态筛选

- **WHEN** 用户已选择一个工作流，再把执行状态选为「执行中」
- **THEN** 表格只显示该工作流中执行中的记录

#### Scenario: 已删除工作流不占分类

- **WHEN** 一个工作流已被删除，但它仍有历史任务
- **THEN** 顶部分类不再出现该工作流
- **AND** 选择「全部」时仍能看到它的历史记录

### Requirement: 表格采用设备管理表纸样式

任务清单表格 MUST 使用共享表格组件，并采用设备管理表格的实线表纸、无位移阴影、斑马纹、表头图标、固定行高与横向拖拽。表纸强调色 MUST 使用任务清单模块色，MUST NOT 使用设备管理的绿色。每页 MUST 默认显示 5 行，并提供与设备管理一致的页码与翻页控件。页面 MUST NOT 提供卡片视图切换。

#### Scenario: 表格外观对齐设备管理

- **WHEN** 用户打开任务清单
- **THEN** 表格是实线表纸且没有位移硬影
- **AND** 表头含图标，行按固定高度排列

#### Scenario: 分页口径一致

- **WHEN** 工作流记录超过 5 条
- **THEN** 表格默认只显示 5 行
- **AND** 工具栏显示当前页、总页数与总条数
