## ADDED Requirements

### Requirement: File-view chrome uses doodle hard-edge and sketch paper

打开 Android 页面叶子的文件详情时，主工作区的操作按键 MUST 采用硬边按键皮肤（几何与侧栏「退出」一致）。元素定位信息表 MUST 以 SketchTable 表纸呈现（共享 `AppTable` 皮肤、模块强调色 `--c-element`、实线描边）。系统 SHALL NOT 在该页为表格另包 `el-card`，SHALL NOT 把删除操作保留为 Element Plus 默认圆角 plain 危险按钮。列字段、行内编辑与无截图/无分段筛选的契约 MUST 保持成立。

#### Scenario: Delete key matches logout geometry

- **WHEN** 用户打开元素定位项目中的一个 Android 页面叶子并测量「删除」按键
- **THEN** 其 `border-width` 为 `2px`、`border-style` 为 `solid`、四角 `border-radius` 为 `2px`
- **AND** `box-shadow` 为 `2px 2px 0 0` 加墨色且模糊半径为 `0`
- **AND** 悬停时计算 `transform` 呈左上位移 1px，阴影偏移增至 `3px 3px 0 0`

#### Scenario: Element table uses sketch paper

- **WHEN** 该页已保存元素并渲染表格
- **THEN** 表格由共享 `AppTable` 渲染，外框为墨色实线表纸与 `--c-element` 硬阴影
- **AND** 表格外不套 `el-card`
- **AND** 表体计算 transform 旋转为 none
