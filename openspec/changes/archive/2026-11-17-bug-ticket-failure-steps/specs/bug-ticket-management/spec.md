## MODIFIED Requirements

### Requirement: 任务错误自动登记为 BUG 单

系统 SHALL 在任务终态落库后自动登记 BUG 单。当前工作流任务（`assistant_sop`）状态为 `failed` 或 `interrupted` 时 MUST 只登记一张任务级 BUG 单，MUST NOT 按 `Task.result.failed` 中的步骤名或用例标题再拆多张。该单 MUST 保存失败步骤快照：至少包含序号、步骤名、期望结果、实际结果、尝试次数与原因类别。多个步骤没通过时 MUST 全部写入同一张单，标题 MUST 使用第一个失败步骤名。

历史 `device_control` 任务状态为 `failed` 且没有失败步骤快照时，MUST 继续按 `Task.result.failed` 中的每个失败用例各登记一张；该列表为空时 MUST 登记一张任务级 BUG 单。`interrupted` 且没有失败步骤快照时 MUST 登记一张任务级 BUG 单。用例编写任务状态为 `failed` 时 MUST 登记一张任务级 BUG 单；任务为 `completed` 但 `Task.result.case_import.status=failed` 时 MUST 登记一张入库失败 BUG 单。

`cancelled` 任务 MUST NOT 登记。登记失败 MUST NOT 改变任务状态、任务结果或验收结论。登记 MUST NOT 回读 HTML 报告或已删除任务来补全失败步骤。

#### Scenario: 工作流多步失败只登记一张

- **WHEN** 一条 `assistant_sop` 任务失败，且结果里有两个没通过的步骤
- **THEN** BUG 台账只新增一张关联该任务的 BUG 单
- **AND** 标题含第一个失败步骤名
- **AND** 该单同时保存两个步骤的序号、步骤名、期望结果、实际结果与尝试次数

#### Scenario: 抛错仍能看出停在哪一类

- **WHEN** 一条运行中的工作流任务因模型拒绝结束，且终态里没有已完成的步骤结论
- **THEN** 新增一张 BUG 单
- **AND** 失败步骤的原因类别为模型拒绝
- **AND** 实际结果是给人读的短句，不是网关原文或堆栈

#### Scenario: 中断任务登记

- **WHEN** 任务因进程退出被标记为 `interrupted`
- **THEN** 新增一张对应分类的 BUG 单
- **AND** 失败步骤写明中断原因
- **AND** 正文不出现「服务重启」

#### Scenario: 多个失败用例逐条登记

- **WHEN** 一条没有失败步骤快照的 UI 自动化任务失败，且 `result.failed` 包含两个用例标题
- **THEN** BUG 台账新增两张 `ui_automation` BUG 单，分别对应用例标题
- **AND** 两张 BUG 单都关联同一个任务编号

#### Scenario: 没有失败用例明细时登记任务级 BUG

- **WHEN** 一条没有失败步骤快照的 UI 自动化任务进入 `failed` 且 `result.failed` 为空
- **THEN** 新增一张任务级 `ui_automation` BUG 单，正文包含任务结果中的原因

#### Scenario: 用例入库失败登记

- **WHEN** 用例编写任务为 `completed` 且 `case_import.status=failed`
- **THEN** 新增一张 `case_authoring` BUG 单，正文包含入库失败原因
- **AND** 任务仍保持 `completed`，验收结论不变

#### Scenario: 取消任务不登记

- **WHEN** 任务被用户取消并进入 `cancelled`
- **THEN** BUG 台账不新增该任务的 BUG 单

### Requirement: 历史任务错误可补录

系统 SHALL 提供历史同步能力，扫描当前用户可见任务中处于 `failed` / `interrupted` 的任务，以及 `completed` 但用例入库失败的任务，按自动登记规则补录 BUG 单。同步 MUST 幂等，并 MUST 返回扫描数、新增数、更新数与跳过数。对已有失败步骤快照的当前工作流任务，同步 MUST 补进同一张任务级 BUG 单，MUST NOT 再按旧的用例来源键拆出新单。已按用例拆开的历史 BUG 单 MUST 保持原样。

#### Scenario: 同步历史失败任务

- **WHEN** 用户点击「同步历史错误」，且存在带失败步骤快照的历史失败任务
- **THEN** 该任务只对应一张任务级 BUG 单
- **AND** 响应包含扫描数、新增数与更新数

#### Scenario: 已拆开的历史单不被合并

- **WHEN** 同一任务下已经存在按用例拆开的 BUG 单，且任务结果里没有失败步骤快照
- **THEN** 再次同步不删除、不合并这些历史单

#### Scenario: 没有历史错误

- **WHEN** 当前用户可见任务中没有可登记的错误
- **THEN** 同步成功返回，新增数为 0，不创建空 BUG 单

### Requirement: BUG 列表的列头图标与首列身份单元

BUG 单列表的列头 MUST 呈现「图标 + 纯文字列名」，图标 SHALL 来自列配置，SHALL NOT 拼接进列名文本。首列 MUST 是一个身份单元：图标圆 + `BUG 编号`（主行）+ 创建时间（副行）；因此系统 SHALL NOT 再单列「创建时间」，同一时间信息 MUST NOT 在表格里出现两次。表格 MUST NOT 绘制列分隔线（`AppTable` 的 `border` MUST 为关闭），行分隔与表头分栏仍由既有表纸皮肤承担。分类、状态与操作列 MUST 保持原有语义与点击行为。关联任务列 MUST 只展示任务编号，MUST NOT 链到 `/tasks/:id`。

#### Scenario: 列头显示图标与纯文字列名

- **WHEN** 用户打开 `/bugs`
- **THEN** 六个列头各自渲染一个图标与其纯文字列名
- **AND** 列名文本本身不含图标字符

#### Scenario: 首列同时给出编号与创建时间

- **WHEN** 查看任一 BUG 行的首列
- **THEN** 该单元同时呈现图标圆、`BUG-xxxx` 编号与创建时间
- **AND** 表格中不存在独立的「创建时间」列

#### Scenario: 表格不画列线

- **WHEN** 检查 BUG 表格的结构与计算样式
- **THEN** `AppTable` 未开启 `border`，不出现竖直列分隔线
- **AND** 行与行之间仍可凭行底色与既有行分隔区分

#### Scenario: 原有交互不变

- **WHEN** 点击「查看」
- **THEN** 打开详情抽屉
- **AND** 点击按键不会同时触发行点击以外的副作用

#### Scenario: 列表不链到已下线的任务详情

- **WHEN** 查看关联任务列
- **THEN** 能看到来源任务编号
- **AND** 该列不存在指向 `/tasks/:id` 的链接

## ADDED Requirements

### Requirement: BUG 单保存失败步骤四问

系统 SHALL 为带失败步骤快照的 BUG 单持久化每一步的序号、步骤名、期望结果、实际结果、尝试次数与原因类别。原因类别 MUST 只取：步骤未通过、模型拒绝、设备命令失败、平台错误、已中断。期望结果 MUST 是该步必须达成的结果；没有该文本时 MUST 明确写「未记录」，MUST NOT 留空。实际结果 MUST 是给人读的短句。列表与详情 MUST 返回该快照；没有快照的旧单 MUST 返回空列表，MUST NOT 因此报错。

#### Scenario: 详情能读出四问

- **WHEN** 打开一张由步骤未通过产生的 BUG 单详情
- **THEN** 能读到出错步骤的序号与名称、原因类别「步骤未通过」、期望结果与实际结果
- **AND** 能读到该步的尝试次数

#### Scenario: 旧单没有快照

- **WHEN** 打开一张登记于本能力之前、没有失败步骤快照的 BUG 单
- **THEN** 详情仍返回原来的错误正文
- **AND** 失败步骤列表为空

### Requirement: BUG 单详情按四问展示

带失败步骤快照的详情 MUST 按「出错步骤、原因类别、期望结果、实际结果」展示，MUST NOT 只把快照拼成一段不可分的纯文本。第一个失败步骤 MUST 展开；其余失败步骤 MUST 可展开查看，且默认不占满抽屉。没有快照的旧单 MUST 继续展示原来的错误正文。详情字号仍 MUST 只取 16px 与 14px 两档。错误内容区 MUST 保持既有卡片几何：描边、圆角、硬偏移影与卡内滚动。

#### Scenario: 四问分栏可读

- **WHEN** 打开一张带失败步骤快照的 BUG 单
- **THEN** 页面分别呈现出错步骤、原因类别、期望结果与实际结果
- **AND** 用户不必阅读整段原文才能回答这四问

#### Scenario: 其余失败步骤默认折叠

- **WHEN** 一张单含两个失败步骤
- **THEN** 第一个步骤的四问直接可见
- **AND** 第二个步骤需展开后才显示期望与实际

#### Scenario: 旧单退回原文

- **WHEN** 打开一张没有失败步骤快照的 BUG 单
- **THEN** 详情仍显示原来的错误正文
- **AND** 不出现空白的四问卡

### Requirement: 有报告才提供查看入口

BUG 单详情在来源任务仍有 HTML 报告定位时 MUST 提供「查看报告」，并 MUST 打开该任务已生成的 HTML 报告。没有报告定位，或来源任务已删除时，MUST 只显示任务编号，MUST NOT 链到 `/tasks/:id`，也 MUST NOT 显示不可用的报告按钮。报告入口 MUST NOT 把报告正文复制进 BUG 单。

#### Scenario: 有报告时可以打开

- **WHEN** 打开一张来源任务仍有报告定位的 BUG 单并点击「查看报告」
- **THEN** 打开该任务的 HTML 报告
- **AND** 页面不导航到 `/tasks/:id`

#### Scenario: 没有报告时不给死链

- **WHEN** 打开一张没有报告定位的 BUG 单
- **THEN** 仍能看到来源任务编号
- **AND** 不出现「查看报告」
- **AND** 不存在指向 `/tasks/:id` 的链接
