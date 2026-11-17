## MODIFIED Requirements

### Requirement: 用例字段与枚举取值

用例行 MUST 直接属于一个项目，MUST NOT 再属于目录或用例文件。用例行 MUST 提供以下字段：编号、优先级、系统、业务类型、模块、前置条件、步骤、更新时间。优先级 MUST 取值 `P0` / `P1` / `P2`；系统 MUST 取值 `ANDROID` / `WEB` / `IOS` / `API`；业务类型 MUST 取值 家电 / 照明 / APP。编号 MUST 由系统分配且 MUST NOT 可编辑，格式为 `TC-YYYYMMDD-NNNN`。模块与前置条件 MUST 为可空自由文本。用例 MUST NOT 再提供「类型」「测试类型」与「预期结果」字段。库类型由所属项目决定，MUST NOT 在行上切换。

#### Scenario: 新建行给出合法默认值

- **WHEN** 用户在项目表新建一行且未选择任何枚举
- **THEN** 该行优先级为 `P1`、系统为 `ANDROID`
- **AND** 保存时 MUST NOT 因枚举缺失被拒绝

#### Scenario: 编号不可编辑

- **WHEN** 用户在编号列双击或尝试输入
- **THEN** MUST NOT 进入编辑态，MUST NOT 出现输入框
- **AND** 新建行保存后编号 MUST 由系统按 `TC-YYYYMMDD-NNNN` 生成

#### Scenario: 系统枚举含暂不支持的取值

- **WHEN** 用户展开系统下拉
- **THEN** 选项 MUST 为 ANDROID、WEB、IOS、API 四项
- **AND** IOS 选项 MUST 带「暂不支持执行」标注
- **AND** 选择 IOS 后 MUST 允许保存（不阻断录入）

#### Scenario: 表格不再出现旧字段

- **WHEN** 用户查看项目表的表头
- **THEN** MUST NOT 出现「类型」「测试类型」列与「预期结果」列
- **AND** 表头 MUST 含「优先级」「系统」「业务类型」「步骤」

### Requirement: 步骤序列的结构与保存语义

每条用例 MUST 拥有一个有序步骤序列；每一步 MUST 包含动作（`action`）与断言（`assertion`）两个文本字段。自动化项目的步骤 MAY 携带两个可选执行提示：页面锚点（`anchor`）与日志证据（`log`）。功能项目的步骤 MUST NOT 接受这两个执行提示。执行提示 MUST 与动作、断言一同保存与读回，MUST NOT 参与动作/断言的非空与长度校验。`anchor` 的键 MUST 限定为 `page` / `entry` / `target`，每个值 MUST NOT 超过 120 字；`log` MUST 含 `sku`（非空文本）、`port`（正整数）与 `keywords`（1 至 6 个，字符集为字母、数字、下划线、点与短横），也 MUST 接受单个 `keyword` 写法。执行提示不合法时 MUST 拒绝保存，且 MUST 指出失败步骤的序号。步骤顺序 MUST 由其在序列中的位置决定，客户端 MUST NOT 直接指定序号。保存用例时 MUST 以完整序列提交并整段替换：保存后服务端的步骤集合 MUST 与提交内容完全一致，未出现在提交中的旧步骤 MUST 被删除。步骤写入 MUST 与用例字段写入同属一个事务，任一失败 MUST 整体不生效，MUST NOT 留下半截步骤。读取 MUST 一次性返回步骤序列（含执行提示），且单次项目表请求的数据库查询次数 MUST NOT 随用例行数线性增长。

#### Scenario: 保存三步并保持顺序

- **WHEN** 用户提交含 3 条步骤的用例，动作依次为 A、B、C
- **THEN** 再次读取该用例 MUST 按 A、B、C 返回 3 条步骤
- **AND** 步骤序号 MUST 为 1、2、3

#### Scenario: 整段替换会删除缺席步骤

- **WHEN** 原用例有 3 步，用户删除第 2 步后保存剩余 2 步
- **THEN** 该用例 MUST 只剩 2 条步骤
- **AND** MUST NOT 残留被删除的步骤

#### Scenario: 保存失败不留半截

- **WHEN** 提交的步骤中第 2 步断言为空而导致校验失败
- **THEN** 该用例的步骤 MUST 保持提交前状态
- **AND** 接口 MUST 返回失败状态与错误定位

#### Scenario: 列表读取不随行数放大

- **WHEN** 一个项目包含 200 条用例、每行平均 5 步
- **THEN** 单次项目表请求的数据库查询次数 MUST NOT 随行数线性增长
- **AND** 响应 MUST 为每行给出只读的步骤数

#### Scenario: 执行提示随步骤保存与读回

- **WHEN** 用户在自动化项目保存某步带 `anchor` 与 `log` 的用例
- **THEN** 再次读取时该步的执行提示与保存前一致
- **AND** 该步的动作与断言文本不因执行提示而改变

#### Scenario: 执行提示非法被拒

- **WHEN** 提交的某步 `anchor` 含未知键，或 `log` 缺少 `sku` / `port` 非法 / 关键词超过 6 个，或功能项目提交了执行提示
- **THEN** 接口 MUST 拒绝保存并指出失败步骤序号
- **AND** MUST NOT 落库

### Requirement: 步骤编辑面板

项目表 MUST NOT 在单元格内展开步骤全文；「步骤」列 MUST 只呈现该用例的步骤条数摘要。用户 MUST 通过一个独立面板（抽屉或弹层）查看与编辑完整步骤序列，该面板 MUST 支持新增、删除与上下移动步骤。面板内的修改 MUST 先落在该行的草稿中，只有用户确认应用后才写回该行；面板内 MUST NOT 单独向服务端提交写请求。

#### Scenario: 表格只显示步数摘要

- **WHEN** 某用例有 2 步
- **THEN** 「步骤」单元格 MUST 为步数摘要（如「2 步」）
- **AND** MUST NOT 在行内展开动作与断言全文

#### Scenario: 面板内可调整顺序

- **WHEN** 用户在面板内把第 2 步上移到第 1 位并点击应用
- **THEN** 该行草稿的动作顺序 MUST 交换为 B、A
- **AND** 表格 MUST 仍显示步数摘要

#### Scenario: 面板内不单独提交

- **WHEN** 用户打开面板、新增 1 步并点击应用，但未点击页面的「保存」
- **THEN** MUST NOT 发出任何写请求
- **AND** 该行 MUST 标记为未保存变更

## REMOVED Requirements

### Requirement: 旧用例数据迁移映射

**Reason**: 现有用例行不再使用，本次清空后不保留旧字段映射。
**Migration**: 升级时删除既有用例行、目录和文件。新数据从空项目表开始，不回填旧编号。
