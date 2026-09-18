## Context

设备引擎已收敛为 uiautomator2 单栈（U2Engine，见 remove-airtest 迁移）。剩余 7 处 raw_handle（.u2）泄露在：DevicePool.u2d(1) · DeviceAdapter.d(1) · DeviceConnection.u2(2) · recovery(3)。UiEngine 协议已覆盖大部分操作，但缺 4 类能力阻塞上层迁移（见 P1）。

## Goals / Non-Goals

**Goals:**
- 补齐 UiEngine 协议缺口（XPath 定位/查询、Toast 完整、分辨率）。
- 上层 7 处 .u2 裸句柄全部改走协议，raw_handle 白名单清零。

**Non-Goals:**
- 不改执行器行为语义（click/swipe/xpath/toast 行为等价）。
- 不引入新引擎实现（仍只 U2Engine）。

## Decisions

1. **协议扩展 = 直接在 UiEngine 加方法**（引擎内部用 u2.xpath 实现），不在上层写 xpath 匹配逻辑——定位细节留在引擎层，符合边界精神。
2. **DeviceConnection 保留，改造成 engine holder**：`DeviceConnection(serial, engine)`，最小改动，执行器/单步调试仍经它取设备能力。
3. **DeviceAdapter 用 engine 替代 self.d**：20 处裸调用映射到协议方法（xpath→query_xpath/click_xpath、toast→get_toast_message、shell/swipe/start/stop→协议原语）。
4. **DevicePool.u2d 改返回 engine**（单步调试经 engine 取能力），recovery 改 engine.is_alive / engine.reconnect。

## 模块防火墙自检

```
apps/* ──✅──→ engines.device.base（UiEngine 协议）+ engines.device.registry（工厂）
apps/* ──❌──→ engines.device.android.u2（具体实现）/ engine.u2 裸句柄
```

## Risks / Trade-offs

- [DeviceAdapter 是执行核心] → P3 迁移后真机跑通 UI 用例全链路（≥2 次）；golden 行为样例前置固化。
- [query_xpath 语义] → u2 xpath.all() 返回 lxml 元素，引擎内转 Node；get_text 走 attrib。
- [toast 兼容] → u2 toast.get_message(0) 语义保留；无 toast 返回空串。

## Migration Plan

按 tasks.md P1→P2→P3→P4：协议扩展（低风险增量）→ DeviceConnection 改 holder → DeviceAdapter 迁移（高风险核心）→ 收尾。每阶段 ruff + check + boundary 验证。
