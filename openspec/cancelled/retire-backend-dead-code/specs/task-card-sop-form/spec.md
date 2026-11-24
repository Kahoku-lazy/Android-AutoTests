# task-card-sop-form Delta

## MODIFIED Requirements

### Requirement: 弹窗提交载荷按用例来源区分

提交时前端 MUST 以 multipart 发送 `title`、`workflow_id` 与 `case_source`（`platform` 或 `yaml`）。来源为 `platform` 时 MUST 额外发送 `case_ids`（JSON 数组字符串），MUST NOT 发送 `config` 文件。来源为 `yaml` 时 MUST 额外发送 `config` 文件，MUST NOT 发送 `case_ids`； MAY 附带 `material` 需求材料文件。选中设备时 MUST 发送 `device_serial`。两种来源 MUST NOT 发送 `agent_id`、`device_label`、`case_title`、`goal`、`documents`、`assistant_route`（智能体直提时代字段已退役）。后端 MUST 拒绝缺失 `workflow_id` 的提交。设备下拉 MUST 展示可连地址（有型号时附带型号）。选中 USB 设备时 `device_serial` MUST 为该 USB 序列号；选中局域网设备时 `device_serial` MUST 为 `IP:端口`；提交值 MUST NOT 是从 `_adb-tls-connect._tcp` 别名拆出的硬件序列号。

#### Scenario: 平台用例来源的提交字段

- **WHEN** 用户选择 2 条平台用例、设备与工作流后提交
- **THEN** 请求体含 title、workflow_id、device_serial、case_source=platform 与 case_ids 数组
- **AND** 请求体不含 config 文件与 agent_id

#### Scenario: 本地 YAML 来源的提交字段

- **WHEN** 用户上传 YAML 后提交
- **THEN** 请求体含 title、workflow_id、device_serial、case_source=yaml 与 config 文件
- **AND** 请求体不含 case_ids 与 agent_id

#### Scenario: 缺失工作流被拒绝

- **WHEN** 提交请求未携带 workflow_id
- **THEN** 后端拒绝提交并提示「请从工作流提交任务」，MUST NOT 创建任务

#### Scenario: USB 设备提交序列号

- **WHEN** 用户选择地址为 `R5CT62RH88F` 的设备并提交
- **THEN** 请求中的 device_serial 为 `R5CT62RH88F`

#### Scenario: 局域网设备提交 IP 与端口

- **WHEN** 用户选择地址为 `192.168.35.57:39569` 的设备并提交
- **THEN** 请求中的 device_serial 为 `192.168.35.57:39569`