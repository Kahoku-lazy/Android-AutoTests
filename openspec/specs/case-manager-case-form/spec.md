# case-manager-case-form Specification

## Purpose
定义用例表单的字段集合、四个枚举的取值口径、步骤序列的结构与保存语义、保存前的校验规则，以及旧用例字段升级到新字段时的映射规则，使入库用例具备可筛选、可校验、可被执行侧消费的稳定形状。

## Requirements

### Requirement: 用例字段与枚举取值

用例行 MUST 提供以下字段：编号、优先级、系统、类型、业务类型、模块、前置条件、步骤、更新时间。优先级 MUST 取值 `P0` / `P1` / `P2`；系统 MUST 取值 `ANDROID` / `WEB` / `IOS` / `API`；类型 MUST 取值 `FUNC`（功能）/ `AUTO`（自动化）；业务类型 MUST 取值 家电 / 照明 / APP。编号 MUST 由系统分配且 MUST NOT 可编辑，格式为 `TC-YYYYMMDD-NNNN`。模块与前置条件 MUST 为可空自由文本。用例 MUST NOT 再提供「测试类型」与「预期结果」两个字段。

#### Scenario: 新建行给出合法默认值

- **WHEN** 用户在文件详情页新建一行且未选择任何枚举
- **THEN** 该行优先级为 `P1`、系统为 `ANDROID`、类型为 `AUTO`
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

- **WHEN** 用户查看文件详情页的用例表格表头
- **THEN** MUST NOT 出现「测试类型」列与「预期结果」列
- **AND** 表头 MUST 含「优先级」「系统」「类型」「业务类型」「步骤」

### Requirement: 步骤序列的结构与保存语义

每条用例 MUST 拥有一个有序步骤序列；每一步 MUST 包含动作（`action`）与断言（`assertion`）两个文本字段。步骤顺序 MUST 由其在序列中的位置决定，客户端 MUST NOT 直接指定序号。保存用例时 MUST 以完整序列提交并整段替换：保存后服务端的步骤集合 MUST 与提交内容完全一致，未出现在提交中的旧步骤 MUST 被删除。步骤写入 MUST 与用例字段写入同属一个事务，任一失败 MUST 整体不生效，MUST NOT 留下半截步骤。读取 MUST 一次性返回步骤序列，且单次文件表格请求的数据库查询次数 MUST NOT 随用例行数线性增长。

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

- **WHEN** 一个文件包含 200 条用例、每行平均 5 步
- **THEN** 单次文件表格请求的数据库查询次数 MUST NOT 随用例行数线性增长
- **AND** 响应 MUST 为每行给出只读的步骤数

### Requirement: 步骤编辑面板

文件详情页的用例表格 MUST NOT 在单元格内展开步骤全文；「步骤」列 MUST 只呈现该用例的步骤条数摘要。用户 MUST 通过一个独立面板（抽屉或弹层）查看与编辑完整步骤序列，该面板 MUST 支持新增、删除与上下移动步骤。面板内的修改 MUST 先落在该行的草稿中，只有用户确认应用后才写回该行；面板内 MUST NOT 单独向服务端提交写请求。

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

### Requirement: 保存前校验与错误定位

保存用例 MUST 满足：标题非空；步骤至少 1 条；每步动作非空；每步断言非空；动作与断言单段长度 MUST NOT 超过 2000 字符；枚举取值 MUST 合法。校验失败时接口 MUST 拒绝保存，MUST 在错误信息中给出失败步骤的序号（从 1 开始），且 MUST NOT 落库。服务端校验 MUST 独立生效，MUST NOT 依赖前端校验作为唯一防线。

#### Scenario: 零步骤被拒

- **WHEN** 提交的用例不含任何步骤
- **THEN** 接口 MUST 拒绝保存并返回步骤为空类错误
- **AND** MUST NOT 落库

#### Scenario: 断言为空被拒

- **WHEN** 提交的用例第 2 步断言为空
- **THEN** 接口 MUST 拒绝保存
- **AND** 错误 MUST 指出失败行与步骤序号（如第 2 步）

#### Scenario: 超长文本被拒

- **WHEN** 某步动作长度为 2001 字符
- **THEN** 接口 MUST 拒绝保存并说明 2000 字符上限

#### Scenario: 枚举非法被拒

- **WHEN** 提交的系统取值不在 ANDROID、WEB、IOS、API 之内
- **THEN** 接口 MUST 拒绝保存并列出可选值

### Requirement: 旧用例数据迁移映射

升级 MUST 保留全部既有用例行与编号。旧「测试类型」MUST 按下列映射写入新两维：`app` → 系统 ANDROID、类型 AUTO；`web` → 系统 WEB、类型 FUNC；`api` → 系统 WEB、类型 AUTO；`func` → 系统 ANDROID、类型 FUNC。旧步骤文本 MUST 折叠为该用例的唯一一条步骤动作，其断言 MUST 填入占位文本「（待补充断言）」。旧「预期结果」内容 MUST 丢弃，MUST NOT 折叠进任何字段。迁移 MUST NOT 让任何用例留下零步骤状态。

#### Scenario: app 用例迁移为 ANDROID 与 AUTO

- **WHEN** 旧用例的测试类型为 `app`，迁移完成
- **THEN** 该用例系统 MUST 为 ANDROID、类型 MUST 为 AUTO

#### Scenario: 旧多行步骤折叠为一条

- **WHEN** 旧用例的步骤文本为 4 行
- **THEN** 迁移后该用例 MUST 恰有 1 条步骤
- **AND** 该步动作 MUST 完整包含原来的 4 行文本

#### Scenario: 预期结果被丢弃且断言为占位

- **WHEN** 旧用例的预期结果非空
- **THEN** 迁移后该步断言 MUST 为「（待补充断言）」
- **AND** MUST NOT 有任何字段承载旧的预期结果文本

#### Scenario: 编号与行数不变

- **WHEN** 对比迁移前后的用例集合
- **THEN** 用例行数与每行编号 MUST 完全相同
