## Why

AI 智能体目前能「看」手机屏幕（`capture_page`/`screenshot_page` 抓屏），却**不能「动」手机**——没有启动 App、点击、滑动、返回等任何设备动作工具。而"AI 抓取页面关系、生成工作流"这类任务的前提，是 AI 能驱动设备在页面间导航、并感知每次点击后"跳没跳页"。引擎层（`engines/base.py` 的 `UiEngine`）与 `DeviceSession` 早已具备 `start_app/click/swipe/press_key` 等操作原语，只是没有逐级暴露到 AI 工具层，补齐为纯接口串联的低风险增量。

## What Changes

1. `apps/device_pool` 新增对 AI 可控的设备动作入口：
   - `pool.py` `DevicePool` 补公开包装 `action_start_app` / `action_stop_app` / `action_press_key`（`start_app/stop_app/press_key` 此前只有 `_session()` 私有入口，未对外包装）。
   - `api.py` `__all__` 新增 `use_device(serial)`（切到目标设备 + 可用性/占用校验）与 `device_action(serial, action, ...)`（动作分发，返回当前前台 `package/activity`）。
2. `apps/ai_assistant` 新增平台工具 `device_action`（设备管理分类，`devices/action`，写工具）：对指定设备执行 `start_app/stop_app/click/long_click/swipe/back/input_text/current` 之一，handler 只调 `device_pool.api.device_action`，返回 `app_current()` 供 AI 判定页面跳转。

无 **BREAKING** 变更（新增工具与 api 白名单函数，现有契约不变）。

## 关联文档

- `dev_docs/02-PRD需求/PRD-08-AI助手.md` §4.1（平台业务工具）、§2.6（SSE 流式对话）
- `dev_docs/03-设计与架构/ARCH-08-AI助手.md` §3.2/§3.5（工具编排与工具双通道）
- `dev_docs/02-PRD需求/PRD-03-设备检查器.md`（设备可用性/执行引擎占用保护口径）
- `dev_docs/03-设计与架构/ARCH-03-设备检查器.md` §3.2/§6.1（`_check_device_available` / `ensure_current_device` 占用前缀）
- `dev_docs/02-PRD需求/PRD-02-设备管理.md`、`dev_docs/03-设计与架构/ARCH-02-设备管理.md`（device_pool 设备生命周期与 api 白名单）

## Capabilities

### New Capabilities

- `ai-device-action`: AI 智能体经平台工具控制设备执行 UI 动作（启动/停止 App、点击、长按、滑动、返回、输入文本、读取前台），并受设备在线与执行引擎占用约束。

### Modified Capabilities

（无）

## Impact

- 后端：`apps/device_pool/pool.py`（补 3 个动作包装）、`apps/device_pool/api.py`（`__all__` 增 `use_device`/`device_action`）、`apps/ai_assistant/agent_scope/tool_registry.py`（新增 schema + handler）、`apps/ai_assistant/views/tool_gateway.py`（如需，同步工具网关 action 白名单）
- 测试：`manage.py check` + `ruff check` + `pytest`；`python tools/gen_arch_stats.py --check-boundaries`（跨模块写/import 合规）
