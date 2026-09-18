## MODIFIED Requirements

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
