## MODIFIED Requirements

### Requirement: 只读日志查询工具可被调用

系统 SHALL 提供一个**只读**业务工具 `read_device_log`，使 AI 智能体可按时间与端口查询设备日志。该工具 MUST NOT 改变设备状态、MUST NOT 写库、MUST NOT 建立新的日志连接，也 MUST NOT 启动、恢复或改变任何端口的监听开关状态，只从平台已采集的缓冲中读取。

#### Scenario: 工具箱中可见且可整类启停

- **WHEN** 用户打开 AI 工具箱
- **THEN** 「设备日志」分类下出现该工具，并标记为只读；停用该分类后工具对智能体不可用，重新启用后恢复

#### Scenario: 调用不产生副作用

- **WHEN** 智能体调用该工具查询任意时间段的日志
- **THEN** 设备状态、占用关系与数据库均不发生变化，返回内容仅为日志文本与其结构

#### Scenario: 查询不启动采集

- **WHEN** 某端口处于关闭监听状态，智能体调用该工具查询该端口
- **THEN** 平台 MUST NOT 因此打开该端口的监听，开关状态与端口占用关系保持不变

### Requirement: 按指定端口查询

工具 SHALL 接受一个可选端口入参；不传时 MUST 使用平台配置的日志端口。传入端口与平台已配置的日志来源不一致时，工具 MUST NOT 报错、MUST NOT 去连接该端口，SHALL 返回可读结论「**端口 `<端口号>` 未配置为日志来源**」（该结论 SHALL 出现在返回的 `note` 字段，`conclusion` 为 `port_not_configured`，行数为 0）。传入端口已登记但处于**关闭监听**状态时，工具 MUST NOT 报错、MUST NOT 因此打开监听，SHALL 返回可读结论「**端口 `<端口号>` 已关闭监听**」（`conclusion` 为 `port_disabled`，行数为 0）。返回内容 MUST 标明日志来源（端口 / 通道）。

#### Scenario: 默认端口

- **WHEN** 智能体不传端口调用
- **THEN** 返回平台配置的日志端口（现场为 7005）上的日志，并在结果中标明来源

#### Scenario: 未配置的端口返回可读结论

- **WHEN** 智能体传入一个平台未采集的端口（如 7004）
- **THEN** 返回 `note` 为「端口 7004 未配置为日志来源」、`conclusion` 为 `port_not_configured`、行数为 0 的正常结果，MUST NOT 抛出错误或返回调用失败

#### Scenario: 结论随传入端口变化

- **WHEN** 智能体分别传入 7004 与 7003
- **THEN** 两次返回的 `note` 分别为「端口 7004 未配置为日志来源」与「端口 7003 未配置为日志来源」

#### Scenario: 已关闭监听的端口返回可读结论

- **WHEN** 智能体查询一个已登记但开关为关闭的端口
- **THEN** 返回 `note` 为「端口 7005 已关闭监听」、`conclusion` 为 `port_disabled`、行数为 0 的正常结果，MUST NOT 抛出错误

#### Scenario: 开关打开后恢复返回日志

- **WHEN** 该端口的监听开关被重新打开且设备继续推送日志，智能体再次查询
- **THEN** 返回该端口的日志行，`conclusion` 回到正常取值，MUST NOT 再返回已关闭监听的结论
