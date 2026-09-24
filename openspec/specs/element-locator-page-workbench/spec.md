# element-locator-page-workbench Specification

## Purpose
定义元素定位模块打开 Android 页面叶子后的元素工作台：以全宽表格呈现与编辑该页元素定位信息，不再提供截图圈选或工具栏分段筛选。

## Requirements

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

### Requirement: 元素行增删改接口契约

元素定位模块 MUST 提供元素行的更新、新增与批量删除能力，全部经 `element_locator/api.py` 写库，成功响应 MUST 采用 `{status, data}` 信封。**更新**入参 MUST 只接受收敛后的可编辑字段（元素名称、文本、主定位、测试点），做与前端同口径的逐列校验；出现其它字段（content-desc、class、resource-id、bounds、候选 XPath 等）MUST 返回 HTTP 400 并给出中文原因，MUST NOT 静默忽略后照常写库；非法值 MUST 返回 HTTP 400 且 MUST NOT 改动数据。**新增** MUST 校验「元素名称必填 + resource-id 与 bounds 至少一个」：缺必填 MUST 返回 HTTP 400；与同页既有元素撞 `(page, resource_id, bounds)` 唯一约束时 MUST 返回 HTTP 409；新增入参 MAY 携带文本、主定位与备注。人工写入的主定位 MUST 落为单条主定位表达式并标记为不稳定。**批量删除** MUST 按元素 id 列表整批原子删除：空集合 MUST 返回 HTTP 400，元素不存在 MUST 返回 HTTP 404（且整批不落库），成功 MUST 返回实际删除条数。字段集合与呈现口径见 `element-locator-element-fields`。

#### Scenario: 更新接受定位字段

- **WHEN** 客户端提交某元素的元素名称、文本、主定位与测试点新值
- **THEN** 返回成功信封，库中这些字段已更新
- **AND** 该元素的缩略图、序号与交互标注不被改动

#### Scenario: 更新非法值被拒

- **WHEN** 客户端提交空的主定位表达式，或提交超出模型列宽的文本
- **THEN** 返回 HTTP 400 并带中文原因
- **AND** 库中该元素保持原值

#### Scenario: 更新越界字段被拒

- **WHEN** 客户端提交 content-desc、class、resource-id、bounds 或候选 XPath 字段做更新
- **THEN** 返回 HTTP 400 并带中文原因
- **AND** 库中该元素保持原值

#### Scenario: 新增缺必填被拒

- **WHEN** 客户端新增元素时元素名称留空，或 resource-id 与 bounds 都为空
- **THEN** 返回 HTTP 400 并带中文原因
- **AND** MUST NOT 新增任何行

#### Scenario: 新增撞唯一约束

- **WHEN** 客户端新增的元素与同页既有元素具有相同的 resource-id 与 bounds
- **THEN** 返回 HTTP 409 并带中文原因

#### Scenario: 批量删除原子且返回条数

- **WHEN** 客户端以 3 个合法元素 id 调用批量删除
- **THEN** 返回成功信封并给出删除条数 3，这 3 条元素已从库中消失

#### Scenario: 批量删除空集合或元素不存在

- **WHEN** 客户端提交空集合，或集合中含不存在的元素 id
- **THEN** 分别返回 HTTP 400 与 HTTP 404 并带中文原因
- **AND** MUST NOT 删除任何元素

### Requirement: 元素工作台按收敛字段集呈现

打开 Android 页面叶子时，主工作区 MUST 以表格呈现该页元素定位信息。表格 MUST 包含且仅包含这些列：**缩略图、元素名称、序号、文本、主定位、交互标注、测试点**。缩略图列 MUST 渲染元素缩略图；元素无缩略图或文件已失效时 MUST 显示占位表达，MUST NOT 出现浏览器破图。元素名称列 MUST 绑定元素 `alias`；序号列 MUST 展示该元素保存时的坐标顺序序号；主定位列 MUST 展示保存时选定的那一条主定位表达式，系统 MUST NOT 在页面上从候选定位中另行挑选；交互标注列 MUST 以标注形式展示该元素的七项交互标志（可点击 / 可长按 / 可滚动 / 可勾选 / 已勾选 / 启用 / 可聚焦）。系统 MUST NOT 把 resource-id 与坐标作为列展示。表格 MUST 每页固定 10 行且默认停在第 1 页，MUST 提供「第 X / Y 页 · 共 N 条」与上一页 / 下一页（无可翻页时禁用），SHALL NOT 提供「显示行数」选择器；分页 MUST NOT 改变集合内容。系统 SHALL NOT 在该工作区渲染页面截图叠加层或 `.shot-pane` 圈选面板，SHALL NOT 在该工作区工具栏提供「全部 / 可点击 / 有文本 / 测试点」分段筛选。

#### Scenario: Opening a page file shows only the table

- **WHEN** 用户打开元素定位项目中的一个 Android 页面叶子
- **THEN** 主工作区可见元素表格（或空态/错误态/加载态之一）
- **AND** 不可见截图圈选面板
- **AND** 不可见「全部 / 可点击 / 有文本 / 测试点」分段按钮

#### Scenario: 表头为收敛后的七列

- **WHEN** 该页已保存元素并渲染表头
- **THEN** 表头含缩略图、元素名称、序号、文本、主定位、交互标注与测试点
- **AND** 不含 resource-id 列与坐标列

#### Scenario: 缩略图缺失显示占位

- **WHEN** 某元素没有缩略图或缩略图文件加载失败
- **THEN** 该格显示占位表达，MUST NOT 显示浏览器破图

#### Scenario: Table lists unfiltered page elements

- **WHEN** 该页已保存多个元素，其中部分不可点击、部分无文本、部分未标测试点
- **THEN** 表格跨页展示上述各类元素，不因属性差异被前端筛掉
- **AND** 工具栏若展示数量，其计数为该页元素总数（与「共 N 条」一致），不是当前页行数

#### Scenario: Empty page still has no screenshot pane

- **WHEN** 该页尚无已保存元素
- **THEN** 主工作区展示空态说明
- **AND** 仍不渲染截图圈选面板与分段筛选

#### Scenario: 每页固定 10 行

- **WHEN** 该页共 27 条元素
- **THEN** 表格首屏只渲染 10 行，分页显示「第 1 / 3 页 · 共 27 条」
- **AND** 点「下一页」后渲染第 11–20 行且页码变为 2

#### Scenario: 翻页不改变集合

- **WHEN** 用户从第 1 页翻到第 2 页
- **THEN** 第 2 页展示同一批元素中的下一段，MUST NOT 出现重复行或漏行
- **AND** 元素总数与「共 N 条」不因翻页而变化

### Requirement: 元素行按收敛字段集编辑

表格 MUST 允许用户在行内修改**元素名称、文本、主定位与测试点**并持久化到元素资产；缩略图、序号与交互标注 MUST 保持只读（它们是采集产物）。可编辑单元格 MUST 默认以**纯文本**呈现，MUST NOT 常驻输入框；用户**双击**某个可编辑单元格后才进入编辑态，按 Enter 提交、按 Esc 或失焦取消，提交或取消后 MUST 回到纯文本呈现。每格输入 MUST 逐列校验（字符串长度 MUST NOT 超过模型列宽、元素名称与主定位表达式 MUST 非空）；校验不通过的输入 MUST 被拒绝并给出中文原因，MUST NOT 写库，MUST NOT 用假值覆盖原值。主定位的写入口径 MUST 为**单条主定位**：保存后该元素的 `primary_xpath` 为该表达式，`primary_stable` 为假。单格更新失败后 MUST 以服务端数据重载该页元素，但该重载 MUST NOT 清空用户已勾选的行——只保留仍然存在的元素 id；批量删除成功后 MUST 清空勾选。表格 MUST 支持**新增一行**（元素名称必填，resource-id 与坐标至少填一个）与**勾选多行批量删除**（二次确认、整批原子）；这两个动作的字段集合与写入口径见 `element-locator-element-fields`；新增撞上同页既有去重键时 MUST 展示后端给出的冲突原因（含既有元素的指认信息），MUST NOT 只给泛化提示。加载失败时 MUST 展示错误并允许重试，MUST NOT 静默清空后假装成功。

#### Scenario: Alias and test-point persist from the table

- **WHEN** 用户在表格中修改某行元素名称或切换测试点开关且请求成功
- **THEN** 该行立即反映新值，刷新后仍保持

#### Scenario: 单元格默认纯文本、双击进入编辑

- **WHEN** 用户打开一个含元素的页面叶子，尚未做任何操作
- **THEN** 各可编辑单元格显示纯文本，MUST NOT 显示常驻输入框
- **AND** 用户双击「文本」单元格后，该格变为输入框并取得焦点，其余单元格仍为纯文本
- **AND** 按 Enter 提交成功后、或按 Esc 取消后，该格恢复为纯文本
- **AND** 编辑态失焦同样提交并回到纯文本

#### Scenario: 可编辑列与只读列

- **WHEN** 用户尝试编辑某行的缩略图、序号或交互标注格
- **THEN** 该格不进入编辑态，值不变
- **AND** 元素名称、文本、主定位与测试点四格可双击进入编辑态

#### Scenario: 主定位编辑写为单条主定位

- **WHEN** 用户把某行主定位改为一条表达式并保存成功
- **THEN** 该元素的 `primary_xpath` 为该表达式、`primary_stable` 为假
- **AND** 再次打开该页显示的就是这条表达式

#### Scenario: 非法输入被拒且不写库

- **WHEN** 用户把主定位或元素名称清空，或把文本填到超过模型列宽
- **THEN** 单元格提示中文原因，该行恢复原值
- **AND** 库中该元素 MUST NOT 被改动

#### Scenario: 行内清空元素名称被拒

- **WHEN** 用户双击某行「元素名称」单元格，清空后按 Enter 或失焦提交
- **THEN** 单元格提示中文原因，该行恢复原元素名称
- **AND** 库中该元素的元素名称 MUST NOT 被改动

#### Scenario: 新增一行

- **WHEN** 用户点「+ 新增一行」，填写元素名称与 resource-id（或坐标）并确认
- **THEN** 该页面新增一条元素，列表刷新后可见（在最后一页）

#### Scenario: 新增行缺必填被拒

- **WHEN** 用户新增一行时元素名称留空，或 resource-id 与坐标都留空
- **THEN** 提示必填原因且 MUST NOT 发出写请求
- **AND** 列表 MUST NOT 多出一行

#### Scenario: 新增撞唯一约束时提示指认既有元素

- **WHEN** 用户新增一行，其 resource-id 与坐标和同页既有元素都相同
- **THEN** 工作区展示后端返回的冲突原因
- **AND** 该原因含既有元素的元素名称；既有名称亦为空时含其 id
- **AND** 列表 MUST NOT 多出一行

#### Scenario: 勾选多行批量删除

- **WHEN** 用户勾选 3 行并确认删除
- **THEN** 这 3 条元素被删除，该页其余元素不受影响
- **AND** 勾选被清空，分页与总数刷新

#### Scenario: 单格更新失败不清空勾选

- **WHEN** 用户已勾选 2 行，随后修改其中一行的某格且该次更新失败
- **THEN** 工作区提示失败原因并以服务端数据重载该页元素
- **AND** 这 2 行的勾选状态 MUST 保持

#### Scenario: Load failure is visible

- **WHEN** 页面元素列表请求失败
- **THEN** 工作区展示中文错误信息与重试入口
- **AND** 不展示半截数据或过期结果

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

### Requirement: 右栏的编辑入口唯一且常驻可见

元素定位项目工作台的右栏 MUST 只呈现**一个**「进入页面编辑」入口，MUST NOT 同时出现两个及以上指向同一动作的入口。该入口 MUST 位于预览标题行（右栏顶部），并 MUST 在预览翻页时保持可见，MUST NOT 随表格滚动或翻页滚出视口。右栏页脚 MUST 只承载分页控件，MUST NOT 再放第二个编辑入口。

#### Scenario: 右栏只出现一个编辑入口

- **WHEN** 统计右栏内文案为「进入页面编辑」的按键
- **THEN** 数量恰好为 1

#### Scenario: 翻页后入口仍可见

- **WHEN** 用户把右栏预览翻到最后一页
- **THEN** 「进入页面编辑」入口仍可见且可点击
