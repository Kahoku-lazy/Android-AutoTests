## Why

设备引擎已收敛为 uiautomator2 单栈（Airtest 已移除），但上层仍有 7 处直接访问 `engine.u2` 裸句柄（DevicePool.u2d / DeviceAdapter.d / DeviceConnection.u2 / recovery），绕过 UiEngine 协议。裸句柄泄露使引擎实现无法被替换，且上层代码与 uiautomator2 API 耦合。需补齐协议缺口并重构上层，让设备能力只经 UiEngine 协议消费。

## What Changes

1. 扩展 UiEngine 协议：新增 `click_xpath` / `long_click_xpath` / `query_xpath` / `get_toast_message` / `reset_toast` / `get_resolution`，由 U2Engine 实现。
2. DeviceConnection 改造为「engine holder」：`DeviceConnection(serial, engine)` 替代持 u2 裸句柄。
3. DeviceAdapter 迁移：20 处 u2 裸调用 → UiEngine 协议调用。
4. 收尾：DevicePool.u2d 改返回 engine；recovery 改走 engine.is_alive / engine.reconnect。

**BREAKING**：DeviceConnection 不再暴露 u2 属性；DeviceAdapter 不再暴露 self.d 裸句柄（执行器内部经 engine）。

## 关联文档

- ARCH：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（§七 引擎边界）
- 规则：`android-autotests-rules/references/architecture.md`（L1c 引擎边界、raw_handle 禁令）
- 前置：`openspec/specs/engine-protocol/spec.md`（本 change MODIFY）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `engine-protocol`: 扩展 UiEngine 协议——新增 XPath 定位操作（click_xpath/long_click_xpath/query_xpath）、Toast 完整能力（get_toast_message/reset_toast）、分辨率查询（get_resolution）。

## Impact

- 引擎：`engines/device/base.py`（协议 +6 方法）、`engines/device/android/u2.py`（实现 +6 方法）。
- 上层：`apps/test_runner/executors/ui/{adapter,connect,recovery}.py`、`apps/device_pool/pool.py`、`apps/test_runner/views/task_views.py`。
- 契约测试：`tests/arch` / 引擎契约测试基类（若存在）随协议扩展补充。
- 边界检查：raw_handle 白名单 7 条随迁移逐条删除。
