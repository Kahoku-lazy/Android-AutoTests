## Why

设备扫描把无线调试别名 `adb-…._adb-tls-connect._tcp` 拆成硬件序列号再交给任务。`adb -s` 认不出这个序列号，任务一启动就报设备不存在。能执行的地址必须是 `adb devices` 里状态为 device、且能直接 `-s` 的那一列。

## What Changes

- 设备发现与在线同步不再把以 `_adb-tls-connect._tcp` 结尾的行登记成可选设备。只保留 USB 序列号和 `IP:端口`。
- 新建任务提交的 `device_serial` 必须是这条 adb 地址。USB 例：`R5CT62RH88F`。局域网例：`192.168.35.57:39569`。
- 只因别名被登记、连接地址不是 USB 序列号也不是 `IP:端口` 的旧记录，在下一轮同步后不再出现在可选列表。
- 配对是否可跳过仍可根据别名判断。别名本身不进入设备列表，也不写入任务。

## 关联文档

无独立子需求编号。归属平台总需求中的设备管理（PRD-02）。

## Capabilities

### New Capabilities

- `device-adb-connectable-address`: 设备管理只把 `adb devices` 中可直接连接的 USB 序列号和 `IP:端口` 登记并交给任务。

### Modified Capabilities

- `task-card-sop-form`: 「弹窗提交载荷固定」里，设备下拉提交的值改为这条 adb 可连地址，不再提交从别名拆出的硬件序列号。

## Impact

- `apps/device_pool`：扫描、登记与在线同步过滤别名。配对提示仍可读原始 `adb devices`。
- `frontend/src/modules/ai-assistant`：新建任务设备下拉的提交值。
- 测试：设备发现过滤与任务提交地址。不改开场模板，不改同设备排队规则。
