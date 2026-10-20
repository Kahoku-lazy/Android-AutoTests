## Purpose

设备管理只把 `adb devices` 里能直接连接的地址登记下来并交给任务，避免把无线调试别名拆成硬件序列号后无法执行。

## ADDED Requirements

### Requirement: 只登记可直接连接的 adb 地址
设备发现与在线同步 MUST 只把 `adb devices` 中状态为 device、且能作为 `adb -s` 目标的行登记为可选设备。这样的行 MUST 是 USB 序列号，或形如 `IP:端口` 的地址。以 `_adb-tls-connect._tcp` 结尾的行 MUST NOT 被登记，也 MUST NOT 被拆成硬件序列号后登记。同一轮输出里同时有 USB 序列号、`IP:端口` 和别名时，可选设备 MUST 只含前两类。

#### Scenario: 四行输出只留下两条可连地址
- **WHEN** `adb devices` 同时列出 `R5CT62RH88F`、`192.168.35.57:39569`、`adb-R5CT62RH88F-chgdtV._adb-tls-connect._tcp` 与 `adb-RF8N21MSW7A-7tM54C._adb-tls-connect._tcp`，且四行状态都是 device
- **THEN** 可选设备只有 `R5CT62RH88F` 与 `192.168.35.57:39569`

#### Scenario: 只有别名的设备不进入列表
- **WHEN** 某台设备在 `adb devices` 里只出现 `adb-RF8N21MSW7A-7tM54C._adb-tls-connect._tcp`
- **THEN** 设备列表没有 `RF8N21MSW7A`，也没有这条别名

### Requirement: 别名登记的旧设备退出可选列表
连接地址以 `_adb-tls-connect._tcp` 结尾、且该设备没有另一条 USB 序列号或 `IP:端口` 仍在 `adb devices` 中的记录，下一轮在线同步后 MUST NOT 再出现在可选设备列表。配对是否已经完成的判断 MUST 仍可读这些别名，但判断结果 MUST NOT 把别名写进设备列表或任务。

#### Scenario: 只挂在别名上的记录被同步去掉
- **WHEN** 库里有一台设备，其连接地址是 `adb-RF8N21MSW7A-7tM54C._adb-tls-connect._tcp`，而当前 `adb devices` 没有对应的 USB 序列号或 `IP:端口`
- **THEN** 下一轮同步后，可选设备列表不再包含这台设备

#### Scenario: 配对提示仍能看见别名
- **WHEN** 用户查询某 IP 是否已可跳过配对，且 `adb devices` 含有一条 `_adb-tls-connect._tcp` 别名
- **THEN** 跳过配对的判断可以把该别名算作已发现，设备列表仍不出现这条别名
