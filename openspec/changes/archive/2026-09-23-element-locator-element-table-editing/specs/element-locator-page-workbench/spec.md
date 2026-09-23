## MODIFIED Requirements

### Requirement: Page workbench is a full-width element table

打开 Android 页面叶子时，主工作区 MUST 以表格呈现该页元素定位信息。表格 MUST 至少包含别名、文本、resource-id、XPath、坐标、测试点列。系统 SHALL NOT 在该工作区渲染页面截图叠加层或 `.shot-pane` 圈选面板。系统 SHALL NOT 在该工作区工具栏提供「全部 / 可点击 / 有文本 / 测试点」分段筛选。表格 MUST **每页固定 10 行**且默认停在第 1 页，MUST 提供「第 X / Y 页 · 共 N 条」与上一页 / 下一页（无可翻页时禁用），SHALL NOT 提供「显示行数」选择器。分页 MUST NOT 改变集合内容：被翻页隐藏的元素仍属该页资产，MUST NOT 因属性差异被筛选或丢弃。

#### Scenario: Opening a page file shows only the table

- **WHEN** 用户打开元素定位项目中的一个 Android 页面叶子
- **THEN** 主工作区可见元素表格（或空态/错误态/加载态之一）
- **AND** 不可见截图圈选面板
- **AND** 不可见「全部 / 可点击 / 有文本 / 测试点」分段按钮

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

### Requirement: Locator fields remain editable in the table

表格 MUST 允许用户在行内修改每一条元素行的**定位业务字段**：别名、文本、content-desc、class、resource-id、XPath、bounds（坐标）、测试点、备注，并持久化到元素资产；`x` / `y` / `width` / `height` MUST 由 bounds 解析后同步写入。系统列（id / 缩略图 / 创建时间 / depth / index）MUST 保持只读。可编辑单元格 MUST 默认以**纯文本**呈现，MUST NOT 常驻输入框；用户**双击**某个可编辑单元格后才进入编辑态（该格变为输入框并取得焦点），按 Enter 提交、按 Esc 或失焦取消，提交或取消后 MUST 回到纯文本呈现。每格输入 MUST 逐列校验：bounds 必须匹配 `[x1,y1][x2,y2]`、数字列必须为非负整数、字符串长度 MUST NOT 超过模型列宽、XPath 输入必须合法；校验不通过的输入 MUST 被拒绝并给出中文原因，MUST NOT 写库，MUST NOT 用假值覆盖原值。XPath 保存时 MUST 覆盖为单条人工候选。表格 MUST 支持**新增一行**（别名必填，resource-id 与 bounds 至少填一个）与**勾选多行批量删除**（二次确认、整批原子）。加载失败时 MUST 展示错误并允许重试，MUST NOT 静默清空后假装成功。

#### Scenario: Alias and test-point persist from the table

- **WHEN** 用户在表格中修改某行别名或切换测试点开关且请求成功
- **THEN** 该行立即反映新值，刷新后仍保持

#### Scenario: 单元格默认纯文本、双击进入编辑

- **WHEN** 用户打开一个含元素的页面叶子，尚未做任何操作
- **THEN** 各可编辑单元格显示纯文本，MUST NOT 显示常驻输入框
- **AND** 用户双击「文本」单元格后，该格变为输入框并取得焦点，其余单元格仍为纯文本
- **AND** 按 Enter 提交成功后、或按 Esc 取消后，该格恢复为纯文本
- **AND** 编辑态失焦同样提交并回到纯文本

#### Scenario: 各定位列均可编辑并持久化

- **WHEN** 用户逐格修改某行的文本、resource-id、content-desc、class、bounds 或备注并保存成功
- **THEN** 该行立即反映新值，刷新后仍保持
- **AND** 修改 bounds 时该行的 x / y / width / height 与 bounds 一致

#### Scenario: XPath 编辑覆盖为单条人工候选

- **WHEN** 用户把某行 XPath 改为一条表达式并保存成功
- **THEN** 该行的候选列表只剩这一条人工候选，再次打开该页显示的就是这条表达式

#### Scenario: 非法输入被拒且不写库

- **WHEN** 用户把 bounds 填成 `abc`，或把列宽填成负数
- **THEN** 单元格提示中文原因，该行恢复原值
- **AND** 库中该元素 MUST NOT 被改动

#### Scenario: 新增一行

- **WHEN** 用户点「+ 新增一行」，填写别名与 resource-id（或 bounds）并确认
- **THEN** 该页面新增一条元素，列表刷新后可见（在最后一页）

#### Scenario: 新增行缺必填被拒

- **WHEN** 用户新增一行时别名留空，或 resource-id 与 bounds 都留空
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

## ADDED Requirements

### Requirement: 元素行增删改接口契约

元素定位模块 MUST 提供元素行的更新、新增与批量删除能力，全部经 `element_locator/api.py` 写库，成功响应 MUST 采用 `{status, data}` 信封。更新 MUST 接受定位业务字段（别名、文本、content-desc、class、resource-id、XPath、bounds、测试点、备注）并做与前端同口径的逐列校验，非法输入 MUST 返回 HTTP 400 且 MUST NOT 改动数据。新增 MUST 校验「别名必填 + resource-id 与 bounds 至少一个」，缺必填 MUST 返回 HTTP 400；与同页既有元素撞 `(page, resource_id, bounds)` 唯一约束时 MUST 返回 HTTP 409。批量删除 MUST 按元素 id 列表整批原子删除：空集合 MUST 返回 HTTP 400，元素不存在 MUST 返回 HTTP 404（且整批不落库），成功 MUST 返回实际删除条数。

#### Scenario: 更新接受定位字段

- **WHEN** 客户端提交某元素的文本、resource-id、bounds 与 XPath 新值
- **THEN** 返回成功信封，库中这些字段已更新
- **AND** bounds 对应的坐标分量与之一致

#### Scenario: 更新非法值被拒

- **WHEN** 客户端提交格式非法的 bounds 或负数尺寸
- **THEN** 返回 HTTP 400 并带中文原因
- **AND** 库中该元素保持原值

#### Scenario: 新增缺必填被拒

- **WHEN** 客户端新增元素时别名留空，或 resource-id 与 bounds 都为空
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
