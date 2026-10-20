## Context

见 proposal.md 的 Why。行为以 `specs/device-adb-connectable-address/spec.md` 与 `specs/task-card-sop-form/spec.md` 为准。`DeviceDetector.adb_device_serials()` 现在收集全部状态为 device 的行，含 `adb-…._adb-tls-connect._tcp`。`resolve_serial()` 对这种别名取 `ro.serialno`，取不到就从别名拆出硬件序列号，并把它登记成设备。新建任务下拉提交的是这个 `serial`。配对提示 `wireless_ready_hint()` 也读这份原始列表。

## Goals / Non-Goals

**Goals:**

- 登记和在线判断只用 USB 序列号与 `IP:端口`。
- 任务提交值与 `adb -s` 能用的地址相同。
- 配对是否可跳过仍能看到别名。

**Non-Goals:**

- 不把同一台手机的 USB 与 `IP:端口` 合并成一条设备。
- 不改开场说明模板，不改按 `device_serial` 排队的规则。
- 不改设备表主键。局域网设备的库内身份仍可以是硬件序列号，只要交给任务的是 `IP:端口`。

## Decisions

### D1：原始列表与可连列表分开

`adb_device_serials()` 继续返回 `adb devices` 里全部 device 行，供配对提示使用。新增一层过滤：去掉以 `_adb-tls-connect._tcp` 结尾的行。`detect()`、扫描登记和在线同步的「是否可见」只用过滤后的集合。

备选：直接改 `adb_device_serials()` 把别名丢掉。否决。配对提示还要靠别名判断「已经发现，可以不填配对码」。

### D2：不再从别名制造序列号

过滤之后，登记循环不会见到别名，`parse_mdns_serial()` 不再参与登记。`IP:端口` 仍按现有方式读取 `ro.serialno` 作为库内身份，连接地址保存 `IP:端口`。读不到序列号的 `IP:端口` 继续跳过，不用传输地址顶替身份。

备选：把 `IP:端口` 直接当成主键。否决。端口一变就会变成另一台设备，这正是现有身份字段要避免的。

### D3：任务下拉提交可连地址

设备接口仍返回库内 `serial` 与 `connection_addr`。新建任务选项的提交值取可连地址：有 `IP:端口` 形式的连接地址时用它，否则用 USB 序列号。展示可以带型号。选项值不得是别名，也不得是只从别名拆出的硬件序列号。

备选：把接口里的 `serial` 字段改成可连地址。否决。设备管理页的连接、删除仍用库内序列号当路径参数。

### D4：旧别名记录靠现有同步删除

在线同步用过滤后的集合判断可见。连接地址是别名、且没有另一条 USB 或 `IP:端口` 仍在列表中的记录，走现有的「不可见则删除」路径。不另写清理迁移。

## 模块防火墙自检

- 不新增跨 App import。过滤与同步留在 `device_pool`，任务表单留在前端。
- 不 import 其它 App 的 service / runner。
- 不新增写库入口。删除旧记录沿用 `device_pool` 现有同步。
- 前端不直连数据库。仪表盘不写库。

## Risks / Trade-offs

- [同一台手机同时出现 USB 和 `IP:端口` 时，任务会当成两台设备] → 与「可连地址各算一条」一致。两台可以各自排队，不在本次合并。
- [只以别名在线的手机从列表消失，用户需要改用 `IP:端口` 或 USB] → 别名本来就不能 `adb -s` 成硬件序列号。配对提示仍告诉用户可以填连接端口。
- [历史任务上已经写入的 `RF8N21MSW7A` 不会改写] → 只影响之后的扫描和新建任务。

## Migration Plan

无表结构迁移。发布后的下一轮设备同步会去掉只挂在别名上的记录。回滚时恢复「别名也登记」的扫描口径；已删记录需重新扫描才会出现。
