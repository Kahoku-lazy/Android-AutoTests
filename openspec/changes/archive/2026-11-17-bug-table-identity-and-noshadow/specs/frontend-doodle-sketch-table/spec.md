## MODIFIED Requirements

### Requirement: Sketch table is AppTable paper skin for existing list pages

名为 SketchTable 的表纸 MUST 是共享 `AppTable` 的视觉皮肤（墨色描边、近直角、无模糊的模块色硬阴影、表体不旋转），SHALL NOT 新增第二个通用表格组件，也 SHALL NOT 在页面上再包一层 Element Plus `el-card` 当作表纸。模块色硬阴影 MUST 取该模块的 `--c-*` 令牌（报告 `--c-report`）。表纸描边的**线型**（`dashed` / `solid`）SHALL 按页登记：设备管理页为**实线**、报告列表为**虚线**。登记线型 MUST 只覆写 `border-style`，描边宽度与颜色仍取共享令牌 `--comp-sheet-border`；模块 SHALL NOT 另写描边宽度、颜色或圆角的字面量。硬阴影 MUST 按页登记「无影页清单」：当前登记为**设备管理页**与 **BUG 单管理页**，这两页的表纸 MUST NOT 绘制模块色位移硬影；其余含表纸的页面（报告列表等）MUST 保留硬阴影。

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
