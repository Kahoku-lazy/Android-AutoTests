## Why

纯规则结构分析（已上线）能识别 6 层分区、XPath、交互指标，但无法理解业务语义——`ivGateway` 这类 resource-id 只能原样展示，无法翻译成「网关入口」，也无法识别「设备卡片 = 名称 + 状态 + 开关 + 连接图标」这类重复结构，更无法一句话总结页面意图。需要借助平台 AI 助手的大模型能力，在纯规则骨架之上叠加语义层，让结构分析结果可读、可理解、可直接用于自然语言交互。

## What Changes

- 新增 `llm_semantic` 模块：LLM 语义抽取器，基于 AgentScope 内置 `generate_structured_output`（Pydantic 模型约束 + 自动校验）。
- 新增 `analyze_page` AI 工具：抓取页面 → 纯规则分区 → LLM 语义增强 → 结构化结果（功能名/卡片角色/页面意图）。
- 复用已上线的 `algorithms/layout.classify_structure` 作为纯规则骨架，LLM 只做语义层。
- 降级保证：LLM 失败 / 校验失败 / model 未透传 → 自动回退纯规则结果，不报错、不影响可用性。
- 前端「结构分析」按钮保持纯规则不变；LLM 语义只在 AI 助手对话入口触发。

## 关联文档

- `ARCH-08-AI助手.md`：AI 工具编排、AgentScope 进程内、tool_registry 单一真相源、SSE 流。
- `ARCH-03-设备检查器.md`：快照抓取链路、结构分析端点、算法下沉。
- `PRD-08-AI助手.md`：AI 助手需求与工具契约。

## Capabilities

### New Capabilities
- `page-analysis-semantic`: 页面结构分析的 LLM 语义增强——功能名命名（resource-id → 中文名）、卡片角色识别、页面意图总结，以及降级回退纯规则的行为约定。

### Modified Capabilities
<!-- 无需求级变化：本变更新增独立能力，不改动已有 device-session / engine-protocol 需求 -->

## Impact

- **后端**：`apps/ai_assistant/agent_scope/`（新增 `llm_semantic.py`；修改 `tool_registry.py`、`in_process_tool.py`、`agent_factory.py` 以透传 model）。
- **复用**：`algorithms/layout.py`、`apps/device_inspector/api.py`（capture_snapshot / analyze_snapshot）。
- **测试**：`llm_semantic` 纯函数单测（假 model：正常 / 降级 / 幻觉）、工具注册与 model 透传链路单测。
- **无**：新增 WS/SSE 通道、新增数据表（命名缓存缓做）、前端改动。
