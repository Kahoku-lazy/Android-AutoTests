## MODIFIED Requirements

### Requirement: 元素表在工作台右栏复用

元素定位项目工作台的右栏 MUST 以**只读预览**的形式呈现选中页面的元素，且预览 MUST 只包含三列：**缩略图 · 元素名称 · 序号**，由共享 `AppTable` 渲染、模块强调色 `--c-element`、实线描边表纸。「文本 / 主定位 / 交互标注 / 测试点」四列 MUST NOT 出现在右栏，MUST 只在文件详情页（`/elements/projects/:code/files/:fileId`）呈现。右栏 MUST 通过分页让该页的**全部**元素都可浏览：每页固定 10 行，MUST 提供「第 X / Y 页 · 共 N 条」文案与上一页 / 下一页（到边界时对应按键 MUST 禁用），MUST NOT 只呈现首屏若干条而无从看到其余元素。右栏 MUST NOT 提供任何编辑能力：MUST NOT 有行内可编辑单元格、MUST NOT 有行勾选框、MUST NOT 有新增行 / 批量删除按键、MUST NOT 有测试点开关；上述编辑能力 MUST 只保留在文件详情页并沿用既有写入口径。右栏 MUST 提供进入该页面编辑的入口，点击后 MUST 跳转到该页面的文件详情路由。缩略图缺失或加载失败时 MUST 落占位表达，MUST NOT 出现浏览器破图。

#### Scenario: 右栏表格与详情页同一张表纸

- **WHEN** 宽屏用户在工作台右栏打开一个已保存元素的页面
- **THEN** 右栏表格由共享 `AppTable` 渲染，外框为墨色实线表纸与 `--c-element` 硬阴影
- **AND** 表头恰好三列：缩略图、元素名称、序号
- **AND** 表头 MUST NOT 出现文本、主定位、交互标注、测试点
- **AND** 表体计算 transform 旋转为 none

#### Scenario: 右栏不可编辑

- **WHEN** 用户在右栏表格里双击任一单元格
- **THEN** MUST NOT 出现输入框，也 MUST NOT 进入编辑态
- **AND** 右栏 MUST NOT 出现行勾选框、「新增一行」、「批量删除」与测试点开关
- **AND** MUST NOT 发出任何写请求

#### Scenario: 从右栏进入页面编辑

- **WHEN** 用户点击右栏的「进入页面编辑」入口
- **THEN** 浏览器地址变为 `/elements/projects/:code/files/:fileId`
- **AND** 该页面呈现可编辑的七列元素表（含文本、主定位、交互标注、测试点，且行内编辑、新增、批量删除、测试点开关齐备）

#### Scenario: 预览只呈现部分并标注总数

- **WHEN** 某页面共有 13 条元素、右栏预览每页呈现 10 行
- **THEN** 右栏 MUST 标注总条数与当前页码（「第 X / Y 页 · 共 N 条」）
- **AND** 其余条数 MUST 可通过「下一页」到达，MUST NOT 存在看不到的元素
- **AND** 到首页 / 末页时对应的翻页按键 MUST 禁用

#### Scenario: 右栏放不下时横向滚动

- **WHEN** 右栏可用宽度小于三列的最小内容宽度（极窄并置场景）
- **THEN** 表格容器出现横向滚动
- **AND** 三列 MUST NOT 被压缩到内容不可读，MUST NOT 被删减

#### Scenario: 右栏按键沿用硬边皮肤

- **WHEN** 测量右栏内「进入页面编辑」入口按键
- **THEN** 其 `border-width` 为 `2px`、`border-style` 为 `solid`、四角 `border-radius` 为 `2px`
- **AND** `box-shadow` 为 `2px 2px 0 0` 加墨色且模糊半径为 `0`
