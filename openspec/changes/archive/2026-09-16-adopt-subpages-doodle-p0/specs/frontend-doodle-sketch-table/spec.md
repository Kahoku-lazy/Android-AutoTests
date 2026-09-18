## Purpose

定义 L4 扁列表的 SketchTable 表纸皮肤：仍由共享 `AppTable` 渲染，外框为虚线纸面加模块色硬阴影，供设备管理与报告列表共用，禁止为「涂鸦表」另建第二套表格封装。

## ADDED Requirements

### Requirement: Sketch table is AppTable paper skin

名为 SketchTable 的表纸 MUST 是共享 `AppTable` 的视觉皮肤（虚线墨色描边、近直角、无模糊的模块色硬阴影、表体不旋转），SHALL NOT 新增第二个通用表格组件，也 SHALL NOT 在页面上再包一层 Element Plus `el-card` 当作表纸。模块色硬阴影 MUST 取该模块的 `--c-*` 令牌（设备 `--c-device`，报告 `--c-report`）。

#### Scenario: Device list table uses sketch paper

- **WHEN** 用户打开 `/devices` 并切换到表格视图
- **THEN** 设备列表由 `AppTable` 渲染，外框为虚线表纸与 `--c-device` 硬阴影
- **AND** 表格外不再套 `el-card`

#### Scenario: Report list table uses the same paper language

- **WHEN** 用户打开 `/reports` 列表
- **THEN** 报告表由 `AppTable` 渲染，外框为虚线表纸与 `--c-report` 硬阴影
- **AND** 不存在名为 SketchTable 的第二套表格封装文件

#### Scenario: Table body does not tilt

- **WHEN** 表纸出现在设备或报告列表
- **THEN** 表体与表头的计算 transform 旋转为 none
- **AND** 硬阴影仍可见

### Requirement: Sketch table tokens are registered

表纸边框、阴影色、纸面底 MUST 引用 `tokens.css` 已登记令牌（颜色原子或 `--comp-*` / `--c-*` 别名）。SHALL NOT 在模块或共享表皮肤中直写与已登记色值等价的十六进制字面量。

#### Scenario: Device and report papers differ only by module accent

- **WHEN** 并排比较设备表纸与报告表纸的计算样式
- **THEN** 描边、圆角、阴影偏移规格同源
- **AND** 阴影色分别解析为 `--c-device` 与 `--c-report`
