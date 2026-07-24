# Phone Control Rules — Android-AutoTests

> **获取完整步骤类型列表**：Read `models/step_types.py` → `class StepType(Enum)`。这是唯一真相源，共 28 种。

## 关键设计决策

- **测试执行独立连接**：测试执行时创建独立 u2 连接，不走 DevicePool 单例。原因：长时间异步任务需要隔离的设备连接，不受全局锁影响
- **Dump 3 层回退**：`d.dump_hierarchy()` 依次尝试默认参数 → `compressed=False` → `compressed=False, pretty=True`
- **XML 截断修复**：检测 XML 结尾不是 `>` → `raw.rfind(">")` 截断修复

## 设备状态

ONLINE / BUSY / OFFLINE / DISCONNECTED（4 种）。生命周期：`(new) → ONLINE ⇄ BUSY → OFFLINE / DISCONNECTED → ONLINE`

## 关键容错

| 场景 | 处理 |
|------|------|
| 设备断连 | OFFLINE，API 返回 502 |
| ATX Agent 未运行 | 返回 502，提示启动 uiautomator2 服务 |
| 测试中断 | `should_stop()` 每 100ms 检查，返回 "stopped" |
| 文本输入失败 | set_fastinput_ime → 降级 adb shell input text → 恢复原输入法 |
| dump XML 截断 | `raw.rfind(">")` 截断修复，失败抛 RuntimeError |
| Toast 未出现 | 双重检测：xpath + `d.toast.get_message(0)` |
