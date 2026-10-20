## 1. 可连地址过滤

- [x] 1.1 在 `apps/device_pool` 保留原始 `adb devices` 列表给配对提示，另提供去掉 `_adb-tls-connect._tcp` 的可连列表。`detect()`、扫描登记和在线同步的可见判断改用可连列表。别名不再调用 `parse_mdns_serial()` 登记。验证：用四行样例（`R5CT62RH88F`、`192.168.35.57:39569`、两条 `adb-…._adb-tls-connect._tcp`）断言可连结果只有前两条；只有别名时结果为空；`wireless_ready_hint` 仍能从原始列表看到别名。

## 2. 任务提交值

- [x] 2.1 新建任务设备下拉的提交值改为可连地址：连接地址是 `IP:端口` 时提交该地址，否则提交 USB 序列号。展示可带型号。验证：`TaskBoard.vue` 的选项 value 不再在有 `IP:端口` 时提交库内硬件序列号；USB 样例提交 `R5CT62RH88F`，局域网样例提交 `192.168.35.57:39569`。

## 3. 收口

- [x] 3.1 对改动的 Python 路径跑 `python -m ruff check` 与第 1 节的测试。验证：ruff 与该测试通过。不跑全量回归。
- [x] 3.2 跑 `python tools/gen_arch_stats.py --check-boundaries`。验证：模块边界零违规。
