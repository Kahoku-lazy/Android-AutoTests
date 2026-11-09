## MODIFIED Requirements

### Requirement: 步骤序列的结构与保存语义

每条用例 MUST 拥有一个有序步骤序列；每一步 MUST 包含动作（`action`）与断言（`assertion`）两个文本字段，并 MAY 携带两个可选执行提示：页面锚点（`anchor`）与日志证据（`log`）。执行提示 MUST 与动作、断言一同保存与读回，MUST NOT 参与动作/断言的非空与长度校验。`anchor` 的键 MUST 限定为 `page` / `entry` / `target`，每个值 MUST NOT 超过 120 字；`log` MUST 含 `sku`（非空文本）、`port`（正整数）与 `keywords`（1 至 6 个，字符集为字母、数字、下划线、点与短横），也 MUST 接受单个 `keyword` 写法。执行提示不合法时 MUST 拒绝保存，且 MUST 指出失败步骤的序号。步骤顺序 MUST 由其在序列中的位置决定，客户端 MUST NOT 直接指定序号。保存用例时 MUST 以完整序列提交并整段替换：保存后服务端的步骤集合 MUST 与提交内容完全一致，未出现在提交中的旧步骤 MUST 被删除。步骤写入 MUST 与用例字段写入同属一个事务，任一失败 MUST 整体不生效，MUST NOT 留下半截步骤。读取 MUST 一次性返回步骤序列（含执行提示），且单次文件表格请求的数据库查询次数 MUST NOT 随用例行数线性增长。

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
- **THEN** 单次文件表格请求的数据库查询次数 MUST NOT 随行数线性增长
- **AND** 响应 MUST 为每行给出只读的步骤数

#### Scenario: 执行提示随步骤保存与读回

- **WHEN** 用户保存某步带 `anchor`（页面锚点）与 `log`（日志证据）的用例
- **THEN** 再次读取时该步的执行提示与保存前一致
- **AND** 该步的动作与断言文本不因执行提示而改变

#### Scenario: 执行提示非法被拒

- **WHEN** 提交的某步 `anchor` 含未知键，或 `log` 缺少 `sku` / `port` 非法 / 关键词超过 6 个
- **THEN** 接口 MUST 拒绝保存并指出失败步骤序号
- **AND** MUST NOT 落库
