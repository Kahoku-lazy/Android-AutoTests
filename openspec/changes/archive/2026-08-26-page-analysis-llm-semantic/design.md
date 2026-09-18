## Context

纯规则结构分析已上线：`algorithms/layout.py` 的 `classify_structure`（6 层分区 + WebView 识别 + 指标）+ `device_inspector` 的 `GET /snapshots/{id}/analyze` 端点 + 前端「结构分析」按钮。

本设计在其上叠加 LLM 语义增强，只在 AI 助手对话入口触发。关键现状约束：

- AgentScope 2.0.3 进程内运行，ReAct 循环经 `tool_registry` 的工具调用各模块 `api.py`。
- AI 工具 handler 是 **sync**，经 `InProcessPlatformTool.call()` 的 `asyncio.to_thread` 跑在线程池。
- **既有结构化 JSON 的模式是「工具入参 + handler 校验」**：`save_case` 的 `steps`/`config_json` 是工具入参，模型在 ReAct 里自然生成（`tool_choice='auto'`），深度校验由 handler `validate_steps` 做，**不依赖强制结构化输出**。
- thinking 模式模型（如 `deepseek-v4-flash-vision-exp`）**不支持强制 `tool_choice`**（`generate_structured_output` 内部就是强制 tool_choice），会导致结构化输出不稳定。

## Goals / Non-Goals

**Goals:**
- 给页面元素做语义命名（功能名 / 卡片角色 / 页面意图），供 AI 助手自然语言汇报页面结构。
- 复用 `save_case` 既有的「工具入参 + handler 校验」模式，兼容 thinking / 非 thinking 模型。
- 降级保证：无语义提交时仍有纯规则结果可用。

**Non-Goals:**
- 不改前端「结构分析」按钮（保持纯规则）。
- 不做命名缓存/沉淀（P3 缓做）。
- 不新增 WS/SSE 通道、不新增外部依赖。
- 不引入 `generate_structured_output`（强制 tool_choice，thinking 模式不兼容）。

## Decisions

### D1：语义命名走「工具入参 + handler 校验」，不用 `generate_structured_output`

- **理由**：测试用例 JSON 已验证该模式——JSON 是工具入参，走 `tool_choice='auto'`（thinking 支持），handler 深度校验。`generate_structured_output` 内部强制 tool_choice，thinking 模式拒绝（实测 `400 Thinking mode does not support this tool_choice`）。
- **备选**：`generate_structured_output`（强制结构化）——被否，thinking 模式不稳定。

### D2：拆成两个工具

- **`analyze_page`**（read_only）：capture + 纯规则分区，返回元素（rid/class/text/clickable/role/metrics/xpaths）。**无 LLM 调用**。
- **`save_page_semantic`**（write）：语义命名作为工具入参（`page_summary` + `elements[{resource_id, func_name, metrics}]` + `cards`），handler 校验后合并返回。

Agent ReAct 两步自然完成：`analyze_page` 拿元素 → 模型推理命名 → `save_page_semantic` 提交。镜像 `search_elements → save_case` 的既有编排。

### D3：无 model 透传

- **理由**：语义命名由 Agent 的 ReAct 循环**自然产生**（模型在推理中起名），不再有 handler 内部的嵌套 LLM 调用。因此 `agent_factory` / `in_process_tool` 无需透传 model。
- **移除**：原方案的 model 透传链路（`_build_toolkit`/`build_platform_tools`/`InProcessPlatformTool` 的 model 参数）。

### D4：防幻觉校验在 `save_page_semantic` handler

- handler 校验：`resource_id` 必须属于该快照的元素集合；`metrics` 取值必须在枚举内；`func_name` 可为空（无语义）。
- 与 `save_case` 的 `validate_steps` 同一思路：松 input_schema + handler 深度校验。

### D5：`llm_semantic.py` 改为纯校验模块

- 移除 `extract()`（`generate_structured_output` 调用）。
- 保留/新增 `validate_semantic(semantic, input_elements)` 纯函数：rid 真实性 + metrics 枚举 + 结构清洗，供 handler 复用。

## 模块防火墙自检

- `ai_assistant` import `apps/device_inspector.api`（capture_snapshot / analyze_snapshot，白名单函数）✅。
- `ai_assistant` import `algorithms.layout`（L1a 纯函数）✅。
- `ai_assistant` ❌ 不 import `device_inspector.service / models` 内部实现。
- `save_page_semantic` 为只读合并（本次不落库）；命名缓存若后续做，写库走对应 App `api.py`。
- 前端不参与本变更；无 WS/SSE 新增。

## Risks / Trade-offs

- [语义命名由 Agent 自然语言产出，可能不完整/不规范] → `save_page_semantic` handler 校验（rid 真实性 + metrics 枚举）+ 缺失字段置空，不阻断纯规则结果。
- [thinking 模型在 ReAct 里也可能「光说不动工具」] → 这是 ReAct 通用现象（非本设计引入）；`analyze_page` 本身是纯规则工具，语义缺失不影响结构分析可用。
- [Agent 需两步（analyze → save_semantic），多一次工具往返] → 可接受，与 `search_elements → save_case` 同构。
- [命名缓存未做，重复分析重复推理] → 留 P3，本次不做。
