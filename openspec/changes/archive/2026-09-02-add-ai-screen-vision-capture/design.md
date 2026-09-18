## Context

- 已通部分：用户手动传图（DataBlock → formatter → image_url）、视觉模型接入（`deepseek-v4-flash-vision-exp` 等）、SSE 的 `TOOL_RESULT_DATA_DELTA` 事件、前端 `SSEMessageBuilder` 已累积 `data/mediaType`。
- 缺口：① 无「截屏返回图片」工具；② `in_process_tool._format_result/_make_chunk` 只产出 `TextBlock`，不支持 `DataBlock`；③ 前端 `ToolCallCard` 不渲染 `tool_result.data` 图片；④ `chat_views._dicts_to_blocks` 还原 `tool_result` 时不把 output 内 text/data 字典转回块对象。
- AgentScope 2.0.3 关键能力（已核实源码）：`ToolChunk.content`/`ToolResponse.content` 为 `List[TextBlock | DataBlock]`；formatter `convert_tool_result_to_string` 会把命中 `supported_input_media_types` 的 `DataBlock` 提升为多模态输入并附 `<system-reminder>` 标识；OpenAI/DashScope/Anthropic/Gemini formatter 均把 `DataBlock` 转 image_url。设备检查器 `capture_page_screenshot` 返回 `MEDIA_ROOT` 相对路径 `inspector/shots/capture_{ts}.png`。
- 模型通道（已核实 `agent_factory._build_model`）：仅 `provider == "dashscope"` 走 `DashScopeChatModel`，其余（openai/anthropic/deepseek/gemini/custom）一律走 `OpenAIChatModel`（openai formatter，支持 image_url）；`AIAgent.formatter` 字段（默认 dashscope）当前**未被** agent 构建消费。故 deepseek 视觉模型（`deepseek-v4-flash-vision-exp`）经 openai formatter 可接收图片，无需改配置。

## Goals / Non-Goals

**Goals:**

- 新增只读工具 `screenshot_page`，返回截图图片 + 摘要文字。
- 视觉模型在工具结果中收到截图（像素级）；截图在对话回显；历史还原。

**Non-Goals:**

- 不改 `capture_page` 现有契约；不新增 WS/SSE 通道；单次仅一张截图；不做截图画框标注/OCR 叠加；不让图片作为独立 assistant 回答气泡（图片在工具调用卡内展示）。

## Decisions

**D1：新增只读工具 `screenshot_page`，而非改造 `capture_page`。**
`capture_page` 契约是「返回解析 JSON（元素 + OCR）」，服务结构化定位与文本理解；截图图片是另一类数据，混入会改变契约并让非视觉模型每次抓取背上图片数据。新增工具互补、零破坏。备选：改造 `capture_page` 一并返回图片——被否（破坏契约、增加噪音）。

**D2：工具结果以 `ToolChunk(content=[TextBlock, DataBlock(Base64Source(png))])` 返回图片。**
AgentScope 原生支持、formatter 自动提升给视觉模型、SSE 已能流式传输 `TOOL_RESULT_DATA_DELTA`。备选：只返回图片 URL/本地路径——被否（聊天模型不会自行抓取 URL，无法「看」像素）。

**D3：截屏复用 `device_inspector.api.capture_snapshot`，工具 handler 读 `screenshot_path` 文件转 base64。**
走 api.py 白名单、符合防火墙；不在 ai_assistant 重写 adb 截屏。备选：ai_assistant 直连 adb——被否（违反「AI 不直连设备」红线）。

**D4：图片在 `ToolCallCard` 内渲染（data URI + `el-image` 预览），不作为独立 assistant 图片气泡。**
图片是工具调用产物，归属工具卡片；与现有 `userImages`（仅 user 角色）区分，避免 `MessageBubble` 角色逻辑改动。备选：`MessageBubble` 增加 assistant 图片气泡——留待后续，非本次必需。

**D5：持久化/还原——先以真实视觉模型端到端确认 `tool_result` 图片在 `blocks` JSON 中的落库形态（`output` 为字符串还是块列表），再按需扩展 `_dump_msg_blocks`/`_dicts_to_blocks` 使图片块正确落库与还原。**
`_BLOCK_CLASS_MAP` 已含 `tool_result`，`_dicts_to_blocks` 需补齐 output 内 text/data 字典 → `TextBlock`/`DataBlock` 的还原，保证历史加载后视觉模型仍能引用截图。

**D6：截图必须降采样 + 压缩，并放宽 `tool_result_limit`（实测定案）。**
实测：`screenshot_page` 被正确调用，但返回的原图（1440×3040 PNG ≈ 810KB）经 AgentScope `count_tokens` 按 `len(base64)//4` 计约 27 万 token，超过 `ContextConfig.tool_result_limit` 默认 50000，被 `_split_tool_result_for_compression` 整体卸载（结果只剩 `<<<TRUNCATED>>>` 文本，图片 DataBlock 丢失）。故：① handler 内用 PIL 降采样（长边 ≤1280）+ JPEG q85；② `_build_context_config` 设 `cfg.tool_result_limit = 200000`。二者缺一不可。

## 模块防火墙自检

- ai_assistant 新增 handler 调 `apps.device_inspector.api.capture_snapshot`（api.py 白名单）✅；不 import `device_inspector.service` ✅。
- 快照落库由 `device_inspector.api.capture_snapshot` 内部完成，ai_assistant 不直写 `di_` 表 ✅。
- 前端不直连设备/DB，只消费 SSE + REST ✅。
- 无新增 WS/SSE 通道（复用现有 AI SSE 唯一通道）✅。

## Risks / Trade-offs

- [非视觉模型收到 `DataBlock` 时无法看图] → deepseek 提供商平台内走 openai formatter（支持 image_url），视觉模型可接收图片；非视觉模型由 formatter 降级为文本/本地路径 + 图片回显，不报错。
- [大图 base64 增大请求体/上下文] → 沿用 5MB 图片上限与 16MB 请求体预算；单张截图通常 ≤ 数百 KB。
- [`tool_result` 内 DataBlock 的 SSE 事件流与历史还原需与 AgentScope 2.0.3 对齐] → 实现阶段先跑真实视觉模型端到端，再落前端渲染与还原。
- [截图过大触发 AgentScope 工具结果卸载（`tool_result_limit` 默认 50000 token，图片按 base64/4 计）] → 已按 D6 降采样 + 放宽上限至 200000；上线后若仍见 `<<<TRUNCATED>>>`，进一步下调截图尺寸或上调上限。
