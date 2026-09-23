## Purpose

定义元素定位模块打开 Android 页面叶子后的元素工作台：以全宽表格呈现与编辑该页元素定位信息，不再提供截图圈选或工具栏分段筛选。

## ADDED Requirements

### Requirement: Page workbench is a full-width element table

打开 Android 页面叶子时，主工作区 MUST 以表格呈现该页元素定位信息。表格 MUST 至少包含别名、文本、resource-id、XPath、坐标、测试点列。系统 SHALL NOT 在该工作区渲染页面截图叠加层或 `.shot-pane` 圈选面板。系统 SHALL NOT 在该工作区工具栏提供「全部 / 可点击 / 有文本 / 测试点」分段筛选。列表 MUST 展示该页全部已保存元素（受接口既有条数上限约束），MUST NOT 因前端筛选控件缩小集合。

#### Scenario: Opening a page file shows only the table

- **WHEN** 用户打开元素定位项目中的一个 Android 页面叶子
- **THEN** 主工作区可见元素表格（或空态/错误态/加载态之一）
- **AND** 不可见截图圈选面板
- **AND** 不可见「全部 / 可点击 / 有文本 / 测试点」分段按钮

#### Scenario: Table lists unfiltered page elements

- **WHEN** 该页已保存多个元素，其中部分不可点击、部分无文本、部分未标测试点
- **THEN** 表格同时展示上述各类元素，不因属性差异被前端筛掉
- **AND** 工具栏若展示数量，其计数与表格行数一致

#### Scenario: Empty page still has no screenshot pane

- **WHEN** 该页尚无已保存元素
- **THEN** 主工作区展示空态说明
- **AND** 仍不渲染截图圈选面板与分段筛选

### Requirement: Locator fields remain editable in the table

表格 MUST 允许用户在行内修改元素别名与测试点标记，并持久化到元素资产。其它定位字段（文本、resource-id、XPath、坐标）SHALL 以只读方式展示。加载失败时 MUST 展示错误并允许重试，MUST NOT 静默清空后假装成功。

#### Scenario: Alias and test-point persist from the table

- **WHEN** 用户在表格中修改某行别名或切换测试点开关且请求成功
- **THEN** 该行立即反映新值，刷新后仍保持

#### Scenario: Load failure is visible

- **WHEN** 页面元素列表请求失败
- **THEN** 工作区展示中文错误信息与重试入口
- **AND** 不展示半截截图或过期筛选结果
