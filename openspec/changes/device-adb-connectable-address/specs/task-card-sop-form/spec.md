## MODIFIED Requirements

### Requirement: 弹窗提交载荷固定

提交时前端 MUST 以 multipart 发送：`title`、`agent_id`、`device_serial`、`case_title`（可为空）与 `config` 文件。前端 MUST NOT 再发送 `goal`、`documents` 或 `assistant_route`。设备下拉 MUST 展示可连地址（有型号时附带型号）。选中 USB 设备时 `device_serial` MUST 为该 USB 序列号；选中局域网设备时 `device_serial` MUST 为 `IP:端口`。提交值 MUST NOT 是从 `_adb-tls-connect._tcp` 别名拆出的硬件序列号。

#### Scenario: 提交字段

- **WHEN** 用户填好五项并提交
- **THEN** 请求体含 title、agent_id、device_serial、case_title 与 config，不含 goal、documents、assistant_route

#### Scenario: 用例为空串

- **WHEN** 用户选择「全部用例」后提交
- **THEN** 请求中的 case_title 为空串，表示跑全部用例

#### Scenario: USB 设备提交序列号

- **WHEN** 用户选择地址为 `R5CT62RH88F` 的设备并提交
- **THEN** 请求中的 device_serial 为 `R5CT62RH88F`

#### Scenario: 局域网设备提交 IP 与端口

- **WHEN** 用户选择地址为 `192.168.35.57:39569` 的设备并提交
- **THEN** 请求中的 device_serial 为 `192.168.35.57:39569`
