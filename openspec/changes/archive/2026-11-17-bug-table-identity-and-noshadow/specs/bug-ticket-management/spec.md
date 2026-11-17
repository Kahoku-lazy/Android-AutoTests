## ADDED Requirements

### Requirement: BUG 列表的列头图标与首列身份单元

BUG 单列表的列头 MUST 呈现「图标 + 纯文字列名」，图标 SHALL 来自列配置，SHALL NOT 拼接进列名文本。首列 MUST 是一个身份单元：图标圆 + `BUG 编号`（主行）+ 创建时间（副行）；因此系统 SHALL NOT 再单列「创建时间」，同一时间信息 MUST NOT 在表格里出现两次。表格 MUST NOT 绘制列分隔线（`AppTable` 的 `border` MUST 为关闭），行分隔与表头分栏仍由既有表纸皮肤承担。分类、状态、任务链接与操作列 MUST 保持原有语义与点击行为。

#### Scenario: 列头显示图标与纯文字列名

- **WHEN** 用户打开 `/bugs`
- **THEN** 六个列头各自渲染一个图标与其纯文字列名
- **AND** 列名文本本身不含图标字符

#### Scenario: 首列同时给出编号与创建时间

- **WHEN** 查看任一 BUG 行的首列
- **THEN** 该单元同时呈现图标圆、`BUG-xxxx` 编号与创建时间
- **AND** 表格中不存在独立的「创建时间」列

#### Scenario: 表格不画列线

- **WHEN** 检查 BUG 表格的结构与计算样式
- **THEN** `AppTable` 未开启 `border`，不出现竖直列分隔线
- **AND** 行与行之间仍可凭行底色与既有行分隔区分

#### Scenario: 原有交互不变

- **WHEN** 点击「查看」或「关联任务」链接
- **THEN** 分别打开详情抽屉与跳转 `/tasks/:id`
- **AND** 点击按键不会同时触发行点击以外的副作用
