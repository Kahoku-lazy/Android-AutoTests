## Context

动机见 proposal.md - Why。当前事实（已核对源码）：

- `agent_factory.build_agent()` 只按 `AIAgent.model_name` 建一个模型，`_build_model()` 已能按 model_name 建任意 OpenAI 兼容模型（`OpenAIChatModel`）。
- AgentScope 2.0.3 model 是**无状态配置容器**，`ChatModel.__call__(messages)` 单次文本调用**不强制 tool_choice**；`generate_structured_output()` 内部强制 tool_choice，**thinking 模型（deepseek-v4-pro / deepseek-v4-flash-vision-exp）会报 400**。
- 视觉上下文已现成：工具返回 `DataBlock(Base64Source)`，AgentScope formatter 自动提升给视觉模型；`chat_views._dicts_to_blocks` 已支持历史图片块还原。
- `dashboard/ai_usage.py` 已按 `deepseek-v4-flash-vision-exp` / `deepseek-v4-pro` 计价，路由后用量自动分开。

## Goals / Non-Goals

**Goals:**

- 意图分类交给 AI（`deepseek-v4-pro`）做模糊语义判断，不用关键词规则。
- 按意图选择执行模型：`phone_control`/`workflow` → 视觉模型，`test_case`/`other` → 文本模型。
- 按意图裁剪工具子集；`other` 意图不挂工具。
- 低置信度时反问澄清，不硬路由。

**Non-Goals:**

- 不改 AgentScope 的 ReAct 执行循环、不改 SSE 事件协议。
- 不引入独立分类服务 / 多 Agent 编排（保持现有 in-process 单 Agent-per-turn 形态）。
- 不新增加密/计费逻辑（已由现有 `api.py` / `ai_usage.py` 覆盖）。
- 不做 `test_case`/`other` 的「分类 + 执行合并」优化（留待后续）。

## Decisions

1. **分类器用 `deepseek-v4-pro`**
   - 理由：分类是纯文本模糊判断，pro 便宜且够用；视觉模型看图是执行阶段的事。
   - 备选：用视觉模型分类 → 成本更高、收益为零，弃。

2. **分类走 `model.__call__` + 容错 JSON 解析，不走 `generate_structured_output`**
   - 理由：pro 是 reasoning 档（thinking 模式），强制 tool_choice 会 400。
   - 备选：`generate_structured_output` → 已实测失败（项目笔记），弃。
   - 容错链：正则提取 JSON → 枚举白名单校验 → 失败降级 `other`。

3. **两段式：先 `classify()` 再 `build_agent(intent=...)`**
   - 理由：分类和「选模型」天然分离，最小侵入现有 `_agent_stream`；分类是单次轻量 pro 调用，结果决定 build 参数。
   - 备选：单 Agent + 模型切换中间件 → 复杂且难推理；多 Agent 主从 handoff → 过度设计，弃。

4. **`AIAgent` 加 `vision_model_name` 字段承载视觉模型名**
   - 理由：一个 Agent 同时持有两个模型名，路由表直接读字段；未配置时按默认（空 → 回退 `model_name`）降级为纯文本。
   - 备选：硬编码模型名映射 / 每意图一个 Agent → 前者不可配置、后者违背「单智能体」现状，弃。

5. **工具子集按意图白名单裁剪**
   - 理由：降低幻觉与 token 成本，且 `other` 不挂工具。
   - 映射：`phone_control`→设备/截图工具；`workflow`→页面流/元素工具；`test_case`→用例/执行工具；`other`→空。
   - 备选：全量工具 → 幻觉高，弃。

6. **每轮都过 pro 分类（`test_case`/`other` 不合并）**
   - 理由：最简单、行为一致，先保证正确性。
   - 备选：先跑 pro 再判断是否切 vision（省一次调用）→ 逻辑绕，作为后续优化记录在 Risks。

## 模块防火墙自检

- `intent_router.py`：仅依赖 `agentscope.message`（SystemMsg/UserMsg）+ 模型实例，**无任何跨 App import、无 ORM**。
- `agent_factory.py`：现有改动仅在本模块内（`build_agent` 加 `intent` 参数选 model_name + 工具白名单）；工具 handler 仍经 `tool_registry` 调各 App `api.py`（现有合规链路，不新增跨 App 内部 import）。
- `models.py`：只改 `ai_assistant` 自己的 `ai_agents` 表（加 `vision_model_name`），无跨模块写。
- `serializers.py` / 前端：只加字段透传，无写库旁路。
- 结论：**本设计不触碰防火墙红线**，无新增跨 App 内部实现依赖。

## Risks / Trade-offs

- [thinking 模型强制 tool_choice 报 400] → 分类用 `__call__` + 自然 JSON + 容错解析，禁用 `generate_structured_output`。
- [每轮多一次 pro 分类调用（延迟+成本）] → `test_case`/`other` 后续可合并为「pro 直接执行」，本次先不优化。
- [vision ↔ pro 上下文切换，历史大 base64 截图浪费 token] → 切到 pro 时裁剪截图块，只保留文本。
- [分类幻觉（输出非枚举/编造 intent）] → 枚举白名单校验，非法值降级 `other`；`confidence < 阈值` 反问。
- [控制手机是高危操作] → 视觉模型只输出结构化操作指令，由工具执行器执行；低置信度不硬猜坐标。
- [未配置 `vision_model_name` 的存量 Agent] → 回退 `model_name`，行为同现状（纯文本），不破坏存量。
