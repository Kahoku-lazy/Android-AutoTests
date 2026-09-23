## Why

平台工具调试调用把**所有**异常都折成 400（`views_tool_debug_drf.py` 的 `except Exception` → `ValidationError`）。于是引擎/工具内部故障与「入参写错」返回同一个状态码：排查时会把工具 Bug 误判成参数问题。真实案例是 `list_apps` 撞上 `ShellResponse` 类型违约（已由 `fix-engine-shell-return` 单独修复），前端只看到一句 400。同时该分支**不落任何服务端日志**，故障在现场无痕。

## What Changes

- 新增 500 类异常 `ToolExecutionError(APIException)`：工具/引擎内部故障返回 **5xx**，MUST NOT 再折成 4xx。
- 入参与前置信手可修正的错误（`ValueError`：未知参数、类型转换失败、缺必填、设备未注册等）保持 **400**。
- `except Exception` 分支 MUST 先 `logger.exception` 落日志（含工具名与请求者），再抛 500——错误不得静默忽略。
- `engine-protocol` 不在本单范围；本单只改 AI 工具箱调试调用的错误分类。
- **不**改响应信封（`EnvelopeJSONRenderer` 已把 4xx/5xx 渲染为 `{status:false,message}`）；**不**改前端（服务端 message 的消费由 `fix-tool-debug-error-message` 承接）。

## 关联文档

- PRD-00（需求总纲，AI 工具箱增量）
- 前置变更：`add-platform-tool-debug`（invoke 链路）、`fix-engine-shell-return`（触发本单的真实故障）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-platform-tool-debug`: 新增「调试调用失败按成因区分状态码」要求——入参/前置条件错误 4xx，工具或引擎内部故障 5xx，且内部故障必须留下服务端日志。

## Impact

- 后端：`apps/ai_assistant/views_tool_debug_drf.py`（新增异常类 + 分支改造 + logger）
- 测试：`tests/graybox/unit/test_ai_platform_tool_debug.py`（内部故障 → 500 且落日志；入参错误 → 400 不变）
- 文档：AI 助手接口文档补状态码语义
- 前端 / 迁移 / 依赖：无
