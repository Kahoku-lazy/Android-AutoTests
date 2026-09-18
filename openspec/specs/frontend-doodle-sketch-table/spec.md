# frontend-doodle-sketch-table Specification

## Purpose
定义 L4 扁列表的 SketchTable 表纸皮肤：仍由共享 `AppTable` 渲染，外框为墨色描边（线型按页登记：设备管理页实线、报告列表虚线）加模块色硬阴影，供设备管理与报告列表共用，禁止为「涂鸦表」另建第二套表格封装。

## Requirements

### Requirement: Sketch table is AppTable paper skin

名为 SketchTable 的表纸 MUST 是共享 `AppTable` 的视觉皮肤（墨色描边、近直角、无模糊的模块色硬阴影、表体不旋转），SHALL NOT 新增第二个通用表格组件，也 SHALL NOT 在页面上再包一层 Element Plus `el-card` 当作表纸。模块色硬阴影 MUST 取该模块的 `--c-*` 令牌（设备 `--c-device`，报告 `--c-report`，设备检查器 `--c-element`）。表纸描边的**线型**（`dashed` / `solid`）SHALL 按页登记：设备管理页为**实线**、报告列表为**虚线**、设备检查器为**实线**。登记线型 MUST 只覆写 `border-style`，描边宽度与颜色仍取共享令牌 `--comp-sheet-border`；模块 SHALL NOT 另写描边宽度、颜色或圆角的字面量。

#### Scenario: Device list table uses sketch paper

- **WHEN** 用户打开 `/devices` 并切换到表格视图
- **THEN** 设备列表由 `AppTable` 渲染，外框为**墨色实线**表纸与 `--c-device` 硬阴影
- **AND** 表格外不再套 `el-card`
- **AND** 描边宽度与颜色仍解析为共享令牌 `--comp-sheet-border` 的值（仅 `border-style` 不同）

#### Scenario: Report list table uses the same paper language

- **WHEN** 用户打开 `/reports` 列表
- **THEN** 报告表由 `AppTable` 渲染，外框为**虚线**表纸与 `--c-report` 硬阴影
- **AND** 不存在名为 SketchTable 的第二套表格封装文件

#### Scenario: Table body does not tilt

- **WHEN** 表纸出现在设备或报告列表
- **THEN** 表体与表头的计算 transform 旋转为 none
- **AND** 硬阴影仍可见

#### Scenario: Inspector element table uses the same paper with its module accent

- **WHEN** 用户打开 `/inspector` 并载入任一快照
- **THEN** 元素表格由共享 `AppTable` 渲染，外框为墨色实线表纸与 `--c-element` 硬阴影
- **AND** 描边宽度与颜色仍解析为 `--comp-sheet-border`（仅 `border-style` 覆写为 `solid`），表体无 transform 旋转
- **AND** 页面内不出现 `el-card` 包裹该表格

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
