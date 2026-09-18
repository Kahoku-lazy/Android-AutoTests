## Why

AI 智能体已能经 `capture_page` 工具拿到手机屏幕的**结构化文本**（UI 层级 dump + OCR 文字），但截图图片从不进入模型、也不在对话中展示。即使用户选用视觉大模型，工具回传的仍是纯文本 JSON，视觉能力目前只对用户**手动上传**的图片生效——无法做到「AI 自己截屏 → 视觉模型看像素 → 截图回传对话」的闭环。AgentScope 2.0.3 原生支持工具结果携带多模态图片块（`ToolChunk.content` 可为 `[TextBlock, DataBlock]`），formatter 会把图片自动提升给视觉模型，补齐此链路为低风险增量。

## What Changes

1. 新增只读平台工具 `screenshot_page`（设备检查器分类，`inspector/screenshot`）：对指定在线设备实时截屏，返回**截图图片块（base64 PNG）+ 简要文字**（package/activity/尺寸），并复用设备检查器截屏链路落库快照；`capture_page`（dump/OCR 文本）保持现状不变。
2. 打通工具结果多模态通道：AI 工具层支持返回 `[TextBlock, DataBlock]` 结果，AgentScope formatter 自动把图片提升给视觉模型（OpenAI/DashScope/Anthropic/Gemini 已支持 image_url）。
3. 对话回显：前端 `ToolCallCard` 渲染工具结果中的截图图片（SSE 的 `TOOL_RESULT_DATA_DELTA` 已累积 `data/mediaType`，仅补渲染）。
4. 持久化与上下文还原：assistant 消息 `blocks` 中 `tool_result` 的图片正确落库，历史加载时还原为图片块，供视觉模型后续轮次继续引用。

无 **BREAKING** 变更（新增工具，现有 `capture_page` 契约不变）。

## 关联文档

- `dev_docs/02-PRD需求/PRD-08-AI助手.md` §2.6（SSE 流式对话）、§2.7（消息渲染）、§2.9（图片上传）、§4.1（平台业务工具）
- `dev_docs/03-设计与架构/ARCH-08-AI助手.md` §3.2/§3.3（Agent 构建与 SSE 口径）
- `dev_docs/02-PRD需求/PRD-03-设备检查器.md`（截屏快照链路，复用其 capture）

## Capabilities

### New Capabilities

- `ai-screen-vision`: AI 智能体截取手机屏幕，将截图作为图片喂给视觉模型读取，并在对话中回显该截图。

### Modified Capabilities

（无）

## Impact

- 后端：`apps/ai_assistant/agent_scope/tool_registry.py`（新增 schema + handler）、`in_process_tool.py`（多模态结果格式化）、`views/chat_views.py`（`_dump_msg_blocks`/`_dicts_to_blocks` 图片还原）、`apps/device_inspector/api.py`（复用 `capture_snapshot` 获取 `screenshot_path`）
- 前端：`frontend/src/modules/ai-assistant/components/ToolCallCard.vue`（渲染工具结果图片）
- 测试：`manage.py check` + `ruff check` + `pytest apps/ai_assistant`；`python tools/gen_arch_stats.py --check-boundaries`；前端 `npm run build`；真实视觉模型 + 在线设备端到端验证
