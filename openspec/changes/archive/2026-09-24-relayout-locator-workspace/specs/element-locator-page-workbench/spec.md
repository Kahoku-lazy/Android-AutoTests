## ADDED Requirements

### Requirement: 元素表在工作台右栏复用

元素定位项目工作台的右栏在呈现某个页面的元素时 MUST 复用与文件详情页完全相同的元素表：同一张七列表纸（缩略图 / 元素名称 / 序号 / 文本 / 主定位 / 交互标注 / 测试点），由共享 `AppTable` 渲染、模块强调色 `--c-element`、实线描边表纸。右栏 MUST NOT 为适配窄栏删减列、MUST NOT 另造第二套表格或把列合并。右栏宽度不足以容纳全部列时 MUST 横向滚动，MUST NOT 把列宽压缩到内容不可读。右栏内的操作按键 MUST 采用与文件详情页相同的硬边按键皮肤。

#### Scenario: 右栏表格与详情页同一张表纸

- **WHEN** 宽屏用户在工作台右栏打开一个已保存元素的页面
- **THEN** 右栏表格由共享 `AppTable` 渲染，外框为墨色实线表纸与 `--c-element` 硬阴影
- **AND** 表头列与文件详情页逐列一致（七列）
- **AND** 表体计算 transform 旋转为 none

#### Scenario: 右栏放不下时横向滚动

- **WHEN** 工作台右栏可用宽度小于表格最小内容宽度
- **THEN** 表格容器出现横向滚动
- **AND** 列 MUST NOT 被删减或合并

#### Scenario: 右栏按键沿用硬边皮肤

- **WHEN** 测量右栏内「新增一行」或「删除」按键
- **THEN** 其 `border-width` 为 `2px`、`border-style` 为 `solid`、四角 `border-radius` 为 `2px`
- **AND** `box-shadow` 为 `2px 2px 0 0` 加墨色且模糊半径为 `0`
