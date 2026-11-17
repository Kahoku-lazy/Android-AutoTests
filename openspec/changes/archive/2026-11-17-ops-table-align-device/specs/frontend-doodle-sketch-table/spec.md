## MODIFIED Requirements

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
