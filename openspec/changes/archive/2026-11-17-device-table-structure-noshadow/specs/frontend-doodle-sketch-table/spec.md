## MODIFIED Requirements

### Requirement: Sketch table is AppTable paper skin for existing list pages

名为 SketchTable 的表纸 MUST 是共享 `AppTable` 的视觉皮肤（墨色描边、近直角、无模糊的模块色硬阴影、表体不旋转），SHALL NOT 新增第二个通用表格组件，也 SHALL NOT 在页面上再包一层 Element Plus `el-card` 当作表纸。模块色硬阴影 MUST 取该模块的 `--c-*` 令牌（报告 `--c-report`）。表纸描边的**线型**（`dashed` / `solid`）SHALL 按页登记：设备管理页为**实线**、报告列表为**虚线**。登记线型 MUST 只覆写 `border-style`，描边宽度与颜色仍取共享令牌 `--comp-sheet-border`；模块 SHALL NOT 另写描边宽度、颜色或圆角的字面量。**设备管理页是硬阴影的登记例外：该页表纸 MUST NOT 绘制模块色位移硬影**（见「设备页表纸使用无影变体」）；其余含表纸的页面 MUST 保留硬阴影。

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

## ADDED Requirements

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
