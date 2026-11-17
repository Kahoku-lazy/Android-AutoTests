# frontend-doodle-sketch-table Specification

## Purpose
定义 L4 扁列表的 SketchTable 表纸皮肤：仍由共享 `AppTable` 渲染，外框为墨色描边（线型按页登记：设备管理页实线、报告列表虚线）加模块色硬阴影，供设备管理与报告列表共用，禁止为「涂鸦表」另建第二套表格封装。

## Requirements

### Requirement: Sketch table tokens are registered

表纸边框、阴影色、纸面底 MUST 引用 `tokens.css` 已登记令牌（颜色原子或 `--comp-*` / `--c-*` 别名）。SHALL NOT 在模块或共享表皮肤中直写与已登记色值等价的十六进制字面量。

#### Scenario: Device and report papers differ only by module accent

- **WHEN** 并排比较设备表纸与报告表纸的计算样式
- **THEN** 描边、圆角、阴影偏移规格同源
- **AND** 阴影色分别解析为 `--c-device` 与 `--c-report`

### Requirement: Device table row status is not a first-cell color bar

设备管理页表格的行状态 MUST 只由「状态」列承载（文字标签加状态配色）；SHALL NOT 在首列用 `::before` 一类纯色块作为第二状态载体——它只重复状态列已表达的信息，且对色觉障碍用户不可读。行类名 MUST NOT 在没有样式消费方时保留。

#### Scenario: No color bar on the first cell

- **WHEN** 在浏览器检查 `/devices` 表格任一数据行首列单元格的 `::before` 伪元素
- **THEN** 其 `content` 计算值为 `none`，不渲染任何色块
- **AND** 行状态仍可从「状态」列的标签文字与颜色辨识

#### Scenario: Row classes have no orphan producer

- **WHEN** 检索 `/devices` 表格的行类名与 `AppTable` 的 `row-class-name` 传参
- **THEN** 不存在只为已删除色条服务的行类名（`row-online` / `row-busy`）及其生产函数

### Requirement: Sketch table is AppTable paper skin for existing list pages

名为 SketchTable 的表纸 MUST 是共享 `AppTable` 的视觉皮肤（墨色描边、近直角、无模糊的模块色硬阴影、表体不旋转），SHALL NOT 新增第二个通用表格组件，也 SHALL NOT 在页面上再包一层 Element Plus `el-card` 当作表纸。模块色硬阴影 MUST 取该模块的 `--c-*` 令牌（报告 `--c-report`）。表纸描边的**线型**（`dashed` / `solid`）SHALL 按页登记：设备管理页为**实线**、报告列表为**虚线**。登记线型 MUST 只覆写 `border-style`，描边宽度与颜色仍取共享令牌 `--comp-sheet-border`；模块 SHALL NOT 另写描边宽度、颜色或圆角的字面量。硬阴影 MUST 按页登记「无影页清单」：当前登记为**设备管理页**、**BUG 单管理页**、**运营用户管理页**与**运营模型配置页**，这四页的表纸 MUST NOT 绘制模块色位移硬影；其余含表纸的页面（报告列表等）MUST 保留硬阴影。

#### Scenario: Device list table uses sketch paper

- **WHEN** 用户打开 `/devices` 并切换到表格视图
- **THEN** 设备列表由 `AppTable` 渲染，外框为**墨色实线**表纸
- **AND** 该表纸的计算 `box-shadow` 为 `none`，不呈现模块色位移硬影
- **AND** 表格外不再套 `el-card`
- **AND** 描边宽度与颜色仍解析为共享令牌 `--comp-sheet-border` 的值（仅 `border-style` 不同）

#### Scenario: Report list table uses the same paper language

- **WHEN** 用户打开 `/reports` 列表
- **THEN** 报告表由 `AppTable` 渲染，外框为**虚线**表纸与 `--c-report` 硬阴影
- **AND** 不存在名为 SketchTable 的第二套表格封装文件

#### Scenario: Table body does not tilt

- **WHEN** 表纸出现在设备或报告列表
- **THEN** 表体与表头的计算 transform 旋转为 none
- **AND** 报告列表的硬阴影仍可见

#### Scenario: Ops pages use the shadowless variant

- **WHEN** 用户打开 `/ops/users` 或 `/ops/model-configs`
- **THEN** 两页表纸的计算 `box-shadow` 均为 `none`，不呈现赭橙位移硬影
- **AND** 去影声明限定在运营页根类下，共享表纸皮肤的硬阴影声明未被修改
- **AND** 表纸描边与圆角仍取自共享令牌

### Requirement: Device page paper uses the shadowless variant

设备管理页表纸 MUST 使用**无影变体**：保留共享描边与共享圆角，去掉模块色位移硬影。该变体 MUST 以页面作用域声明（限定在设备页根类下），SHALL NOT 修改共享表纸皮肤 `workbench-theme.css` 的硬阴影声明——共享表纸仍有其它消费方，改共享声明会让它们一并丢影。去影 MUST NOT 波及表内交互元素（`el-button` 的位移硬影保持不变）。该变体 MUST 在表纸皮肤能力中登记，使后续读者不会把它当成漏写。

#### Scenario: Shadow removal is scoped to the device page

- **WHEN** 比较 `/devices` 与 `/reports` 两张表纸的计算 `box-shadow`
- **THEN** 设备页为 `none`，报告页为 `--c-report` 的位移硬影
- **AND** 共享皮肤文件 `shared/styles/workbench-theme.css` 的硬阴影声明未被修改

#### Scenario: Buttons keep their offset shadow

- **WHEN** 检查设备页表格内任意 `el-button`
- **THEN** 该按钮仍呈现 2px 位移硬影与墨色描边

#### Scenario: Frame still separates the paper from the page

- **WHEN** 去影后的表纸出现在设备页
- **THEN** 表纸仍呈现 1px 共享描边（`--comp-sheet-border`）与共享圆角，可与页面底色区分

### Requirement: Bug page paper uses the shadowless variant

BUG 单管理页（`/bugs`）表纸 MUST 使用无影变体：保留共享描边与共享圆角，去掉 `--c-runner` 位移硬影。该变体 MUST 以 BUG 页根类作用域声明，SHALL NOT 修改共享表纸皮肤 `workbench-theme.css` 的硬阴影声明（报告等页面仍靠它）。去影 MUST NOT 波及表内交互元素（`DoodleBtn` 等按键的位移硬影保持不变）。BUG 页 MUST 与设备页共用同一无影口径，SHALL NOT 另造第三种表纸。

#### Scenario: Bug table paper has no hard shadow

- **WHEN** 打开 `/bugs` 并检查 BUG 列表表纸的计算样式
- **THEN** `box-shadow` 为 `none`
- **AND** 描边仍为共享令牌 `--comp-sheet-border` 的值，圆角仍为 `--comp-sheet-radius`

#### Scenario: Bug page removal does not leak to other pages

- **WHEN** 比较 `/bugs` 与 `/reports` 两张表纸的计算 `box-shadow`
- **THEN** BUG 页为 `none`，报告页仍为 `--c-report` 位移硬影
- **AND** 共享皮肤文件 `shared/styles/workbench-theme.css` 未被修改

#### Scenario: Buttons keep their hard edge

- **WHEN** 检查 BUG 表格行内的「查看」按键
- **THEN** 该按键仍呈现墨色描边与位移硬影（沿用 `DoodleBtn` 既有几何）
