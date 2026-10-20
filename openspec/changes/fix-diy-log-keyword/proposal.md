## Why

真机验证发现 DIY 灯效的日志关键词与 H6810 固件实际打印不一致：关键词表登记的是 `diy_configs_set_success`，但 1.6 MB 日志里该词 **0 次命中**，设备每次切换 DIY 灯效实际打印的是 `diy2d_mode stop` / `diy2d_mode_start`（与点击时间点逐一吻合）。结果是「DIY 场景功能」用例稳定被判 FAIL，而 UI 侧其实每次都成功——属于系统性误判。

## What Changes

- 改 `config/device_log_keywords.json`：把 id 23（DIY模式 · DIY灯效设置成功）的关键词从 `diy_configs_set_success` 换成 `diy2d_mode_start`，删除旧词条。
- 不改关键词表结构、不改验收口径、不改工具实现；`check_device_log` 仍按「关键词原文 + 5 秒窗口」判定。
- 改表后需重启平台才生效（关键词表在启动时加载一次）。

## 关联文档

无 PRD 编号：来自 2026-10-20 真机测试（R5CT62RH88F / H6810 / 端口 7005）的实测结论。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无（关键词表的具体词条值不属于行为契约；`device-log-keyword-catalog` 只约束「表格如实展示当前生效的表」，改表内容不改变该契约）。

## Impact

- 配置：`config/device_log_keywords.json`（DIY 一条）。
- 运行期：`check_device_log` 对 DIY 断言改用新关键词，重启后生效。
- 验证：重跑「H6810 场景音乐DIY功能测试」第 4 步（DIY），期望两次点击后 5 秒窗口内命中 `diy2d_mode_start`。
