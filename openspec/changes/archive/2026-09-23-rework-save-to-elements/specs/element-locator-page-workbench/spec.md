## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Page workbench is a full-width element table

**Reason**: 元素定位的元素字段收敛为「缩略图 / 元素名称 / 序号 / 文本 / 主定位 / 交互标注 / 测试点」，原要求把列集合写成「至少包含别名、文本、resource-id、XPath、坐标、测试点列」，与收敛后的呈现口径不再一致。

**Migration**: 由新增要求「元素工作台按收敛字段集呈现」承接——「不渲染截图圈选面板」「不提供分段筛选」「列表展示全部已保存元素」三条不变量逐条保留，并把前置变更 `element-locator-element-table-editing` 交付的「每页固定 10 行分页」「翻页不改变集合」一并承接到新要求中。

### Requirement: Locator fields remain editable in the table

**Reason**: 可编辑面重定义为与呈现列一一对应（元素名称 / 文本 / 主定位 / 测试点）；原要求的可编辑集合（别名、文本、content-desc、class、resource-id、XPath、bounds、测试点、备注）中，content-desc、class、resource-id 与 bounds 已不在收敛后的字段集合内。

**Migration**: 由新增要求「元素行按收敛字段集编辑」承接——「双击进入编辑 / 逐列校验 / 新增一行 / 批量删除 / 加载失败可见」五组行为逐条保留，可编辑列集合与主定位的单条写入口径按收敛口径重写；主定位的字段与接口契约见 `element-locator-element-fields`。

## ADDED Requirements

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

表格 MUST 允许用户在行内修改**元素名称、文本、主定位与测试点**并持久化到元素资产；缩略图、序号与交互标注 MUST 保持只读（它们是采集产物）。可编辑单元格 MUST 默认以**纯文本**呈现，MUST NOT 常驻输入框；用户**双击**某个可编辑单元格后才进入编辑态，按 Enter 提交、按 Esc 或失焦取消，提交或取消后 MUST 回到纯文本呈现。每格输入 MUST 逐列校验（字符串长度 MUST NOT 超过模型列宽、主定位表达式 MUST 非空）；校验不通过的输入 MUST 被拒绝并给出中文原因，MUST NOT 写库，MUST NOT 用假值覆盖原值。主定位的写入口径 MUST 为**单条主定位**：保存后该元素的 `primary_xpath` 为该表达式，`primary_stable` 为假。表格 MUST 支持**新增一行**（元素名称必填，resource-id 与坐标至少填一个）与**勾选多行批量删除**（二次确认、整批原子）；这两个动作的字段集合与写入口径见 `element-locator-element-fields`。加载失败时 MUST 展示错误并允许重试，MUST NOT 静默清空后假装成功。

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

- **WHEN** 用户把主定位清空，或把文本填到超过模型列宽
- **THEN** 单元格提示中文原因，该行恢复原值
- **AND** 库中该元素 MUST NOT 被改动

#### Scenario: 新增一行

- **WHEN** 用户点「+ 新增一行」，填写元素名称与 resource-id（或坐标）并确认
- **THEN** 该页面新增一条元素，列表刷新后可见（在最后一页）

#### Scenario: 新增行缺必填被拒

- **WHEN** 用户新增一行时元素名称留空，或 resource-id 与坐标都留空
- **THEN** 提示必填原因且 MUST NOT 发出写请求
- **AND** 列表 MUST NOT 多出一行

#### Scenario: 勾选多行批量删除

- **WHEN** 用户勾选 3 行并确认删除
- **THEN** 这 3 条元素被删除，该页其余元素不受影响
- **AND** 勾选被清空，分页与总数刷新

#### Scenario: Load failure is visible

- **WHEN** 页面元素列表请求失败
- **THEN** 工作区展示中文错误信息与重试入口
- **AND** 不展示半截数据或过期结果
