## Context

动机见 proposal.md - Why。设计定稿见 `dev_docs/项目笔记/AgentScope/多智能体编排-最终骨架设计.md`。关键事实（已核对源码）：

- AgentScope 2.0.3 的 `Agent` 一次装配：`Agent(name, system_prompt, model, toolkit, context_config, react_config, ...)`——这就是「model + harness」的官方落地。
- 模型实例化按 provider 用专用类：DeepSeek → `DeepSeekChatModel` + `DeepSeekCredential`（含 `thinking_enable`/`reasoning_effort`），统一 `Model(credential=..., model=...)` 模式。当前 `_build_model` 用 `OpenAIChatModel` 包 DeepSeek 是错误用法。
- `FunctionTool`（`tool/_adapters.py`）自动从函数名/docstring/类型注解推导 name/description/schema，支持返回 `ToolChunk(DataBlock(Base64Source))` 传图片给视觉模型，支持 sync/async 函数。
- `ContextConfig.max_image_num` 内置图片数量控制（不需手写裁剪）。
- thinking 模型不支持强制 tool_choice（`400 Thinking mode does not support this tool_choice`），意图识别走 `model.__call__`。

## Goals / Non-Goals

**Goals:**

- 智能体按「model + Harness」拆为 4 套 Harness（意图识别/视觉/推理/强模型），各司其职。
- 意图识别输出 `{intent, intent_code(1/2), prompt}`，按 code 路由，强模型开关短路。
- 工具用 `FunctionTool`（框架能力），模型按 provider 专用类，图片用 `ContextConfig.max_image_num`。
- Django 薄壳：只调用 `agent_scope/` + 存对话记录。

**Non-Goals:**

- 本次不做 skill / MCP / 知识库（移除 rag_service、skill_registry，不预留）。
- 不做智能体间互相通信（TeamSay 类）——本设计是「路由型」：一个对话分给其中一个 Harness，非流水线/团队协作。
- 不做管理员配置前端 UI 的完整实现（先做后端骨架 + 数据模型，前端配置页后续跟进）。

## Decisions

1. **Agent = model + Harness，4 套 Harness**：`intent`（意图识别）、`vision`、`reasoning`、`strong`（多模态强模型）。理由：任务繁杂，单智能体无法有条理；各 Harness 独立 model + 工具 + prompt。
   - 备选：单智能体切模型（已被否定，无法表达"独立身份/工具"）。

2. **意图识别输出 `{intent, intent_code, prompt}`**：`intent_code` 1=视觉/2=推理由模型输出，3=强模型是手动开关（非模型输出）。`prompt` 是模型优化后的精准任务描述，作为下游 Harness 输入。
   - 备选：纯分类标签（不足，下游需要优化后的 prompt）。

3. **模型按 provider 用专用类**：`create_model` 分发 `DeepSeekChatModel`（+`DeepSeekCredential`+`Parameters(thinking_enable/reasoning_effort)`）/ `DashScopeChatModel` / `OpenAIChatModel`。
   - 备选：统一 `OpenAIChatModel` 硬包（丢失 DeepSeek thinking 模式，被否）。

4. **工具用 `FunctionTool`**：平台工具 = 普通函数 handler + `FunctionTool` 包装；图片返回 `ToolChunk(DataBlock(Base64Source))`；权限用 `PlatformFunctionTool` 子类（只读 ALLOW、写 ASK）。
   - 备选：现有 `InProcessPlatformTool` + `TOOL_SCHEMAS` 手动子类（重复造轮子，被否）。

5. **两个模块 + tools 三文件**：`agent_manager.py`（配置+装配）、`model_instance.py`（模型实例+意图路由+执行）、`tools.py`（工具注册表）。Django 只调 `AgentManager` + `run()`。

6. **意图识别走 `model.__call__`**（不强制 tool_choice）+ 容错 JSON 解析，失败降级 `intent_code=2`。

7. **图片控制用 `ContextConfig.max_image_num`**，不手写裁剪。

## 模块防火墙自检

- `agent_manager.py` / `model_instance.py`：只 import `agentscope.*` + 本包内 `tools.py`/`provider_registry.py`，无跨 App import。
- `tools.py`：handler 函数内部经各 App `api.py` 直调（进程内），符合「AgentScope→Tool→api.py」写路径，不碰 service/runner/内部实现。
- `chat_views.py`（薄壳）：只调 `agent_scope` + `save_message`，无智能体逻辑。
- 结论：不触碰防火墙红线；删除 `rag_service`/`skill_registry` 后，`views_knowledge_drf.py` 等知识库入口需同步下线（记录在 tasks）。

## Risks / Trade-offs

- [FunctionTool 权限默认 ASK] → `PlatformFunctionTool` 子类只读 ALLOW、写 ASK。
- [意图识别 thinking 模型不支持强制 tool_choice] → `model.__call__` + 容错解析，失败降级 code=2。
- [工具从 ToolBase 手动子类迁移到 FunctionTool，图片/直调逻辑要重写] → 分阶段：先建 `tools.py` 骨架 + 核心工具，再逐个迁移现有 handler。
- [删除 tool_registry/in_process_tool 破坏既有测试与工具网关] → 同步改写 `tests/ai_assistant/` 依赖测试，工具网关 `tool_gateway.py` 同步下线或改接 `tools.py`。
- [删除 rag_service/skill_registry 影响知识库/技能前端入口] → 本次明确范围为「移除」，相关视图/前端入口一并下线（tasks 中记录）。
