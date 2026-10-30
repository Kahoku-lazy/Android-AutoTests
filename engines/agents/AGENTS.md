# engines/agents AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../AGENTS.md) → **本文件** → 更具体子目录 AGENTS。进入 engines 任务时仍先读上层入口；**冲突时更具体子目录的领域规则优先**。  
> **改本包架构 / 目录职责 / 工具·提示词配置方式时必读。** 完整代码风格正文在 [`.agents/rules/engines-code-style.md`](../../.agents/rules/engines-code-style.md)；**何时读规范、何时用检查技能以下方「AI 阅读与检查流程」及上层 `engines/AGENTS.md` 为准**——勿跳过流程直接改代码。

## 职责

`engines/agents/`：控制设备任务的 SOP / 智能体运行时——角色装配、提示词、工具、消息与计费、工作流、中间件、RAG、语音等。导入边界与上层一致：零 `apps.*`、零 `django.*`（业务能力经注入）。

| 路径 | 职责 |
| --- | --- |
| `config/role_types.py` | Harness 四分段类型（`RoleConfig`/`ToolsConfig`/`ContextConfig`/`ReActConfig`）；装载与装配单向依赖，拆环 |
| `agent_builders.py` | **LLM agents**：`AgentRoleFactory` + `build_*`（再导出四分段类型，过渡期） |
| `realtime_vocie_agent.py` | **Voice agents**：Omni 实时语音角色装配 |
| `config/models.py` | 模型与角色 YAML 装载（`ModelConfig` / `ChatModelFactory` / `load_role_config` / Omni） |
| `config/data/agent_config.yaml` | 角色 ModelConfig + 四分段配置数据 |
| `config/data/prompts/` | 角色系统提示词正文（`*.md`） |
| `config/data/skills/` | 角色 skill |
| `role_sys_prompts.py` | **唯一**角色提示词脚本入口（加载 md + 导出常量） |
| `tools_config.py` | **唯一**角色工具分配入口 |
| `tools/` | 角色工具实现；按模块分组，文件名 `tool_*.py` |
| `messaging/` | 事件上屏、折叠日志、结构化记录、Token 费用；接收方协议见 `event_sink` |
| `mcp_config/` | 角色 MCP 工具配置 |
| `workflow/` | SOP 步骤输入与单次运行；**不在此**创建角色、配置提示词或绑定工具 |
| `middleware/` | 智能体生命周期关键点拦截与扩展 |
| `rag/` | 检索增强；细则见 [`rag/AGENTS.md`](rag/AGENTS.md) |
| `realtime_vocie/` | 知识库语音会话（Omni + RAG）；细则见 [`realtime_vocie/AGENTS.md`](realtime_vocie/AGENTS.md) |

支持的模型系列（配置层）：DeepSeek、Dashscope。

## 创建 Agent 统一流程（必读）

后续新增 LLM / 语音 Agent **必须**按此装配，禁止在 View / workflow 旁路硬编码。

三节点边界（OpenSpec `simplify-basic-agent-role-create` / `agent-basic-role-create`）：

1. **N1 ModelConfig**：YAML 校验 → `ChatModelFactory` → **仅把 `ChatModelBase` 交给 Agent**；`Agent` MUST NOT 接收/持有 `ModelConfig`。
2. **N2 Harness 1:1**：`RoleConfig`=name+system_prompt；`ToolsConfig`=toolkit（**skills 延后**）；`ContextConfig`；`ReActConfig`。类型定义在 `config/role_types.py`（非长期公共 API；`agent_builders` 过渡期再导出）。
3. **N3 Agent vs workflow**：Agent 只提供已装配角色；workflow 编排消费 `build_*`；**本期不清理** workflow `tool_*` 旁路。

步骤：

1. **模型配置**  
   - 在 `config/data/agent_config.yaml` 增加角色节（`ModelConfig` + 下方四分段）。  
   - 由 `config/models.py` 的 `load_role_config` / `ChatModelFactory` / Omni 装载器读取；密钥只存环境变量名。

2. **系统提示词**  
   - 正文写入 `config/data/prompts/<TOKEN>.md`。  
   - YAML `RoleConfig.system_prompt` 写 token；运行时由 `role_sys_prompts.resolve_system_prompt` 解析。  
   - 模块常量 / 类加载器只经 `role_sys_prompts.py` 导出。

3. **角色四分段（`config/role_types.py`）**  
   - `RoleConfig`（name + system_prompt）  
   - `ToolsConfig`（toolkit；空节 `Toolkit()`，设备工具由 `tools_config` 注入；skills DEFERRED）  
   - `ContextConfig` / `ReActConfig`（可空，用默认）

4. **创建运行实例**  
   - **LLM**：`AgentRoleFactory(model_config, role, tools, context, react).create()` → `agentscope.agent.Agent`（内部只传 `model=` 实例）；对外暴露 `build_*() -> Agent`（每次新实例）。实现落点：`agent_builders.py`。  
   - **Voice（Omni）**：`realtime_vocie_agent.build_realtime_vocie_agent()`；会话路径走 `realtime_vocie/`（含 RAG 工具注入）。

5. **工具与技能**  
   - 工具实现：`tools/tool_*.py`；分配：`tools_config.build_*_toolkit()`。  
   - 技能目录：`config/data/skills/`（产品语义本期不扩展 ToolsConfig）。

6. **工作流**  
   - SOP 只编排调用 `build_*`；禁止在 `workflow/` 内创建模型、旁路提示词或直接 import `tool_*`（旁路清理另列变更）。

## 记忆与上下文（现状落点）

Harness「记忆与上下文」**当前没有独立 `memory/` 包**，落点如下（改行为先读对应模块，勿平行再造一套写库记忆）：

| 关切 | 现状落点 |
| --- | --- |
| 角色上下文窗口 / 压缩触发 | `config.role_types.ContextConfig` → AgentScope `ContextConfig` |
| 过程事件上屏、折叠、结构化记录 | `messaging/`（`messages` / `fold` / `record`） |
| Token 与费用 | `messaging/billing.py`；语音侧 session 的 `model_usage` |
| 多轮对话历史（用例/SOP） | 各 `Agent` 运行实例内；**每次 `build_*` 新实例，不跨任务共享** |
| 语音多轮 | `realtime_vocie/` Omni 会话 |
| RAG 知识 | `rag/`：只注入**当轮**上下文（见 `rag/AGENTS.md`） |

## 红线（禁止）

1. **禁止**跳过本文件与下方「AI 阅读与检查流程」直接改本包架构、目录职责或工具/提示词配置方式。
2. **工具**：必须放在 `tools/`，文件名 `tool_xxx.py`；**必须**经 `tools_config.py` 分配；**禁止**业务代码直接 `import` 绑工具。
3. **提示词**：必须经 `role_sys_prompts.py` + `config/data/prompts/*.md`；禁止旁路硬编码。
4. **角色**：新建 LLM 角色经 `AgentRoleFactory` + `agent_builders.build_*`；语音经 `realtime_vocie_agent`；**禁止**恢复已删除的 `role/` 包或 `BaseRole` 旁路。
5. **workflow**：禁止在 `workflow/` 创建角色、配置提示词或绑定工具。
6. **RAG 路径与密钥**：以 [`rag/AGENTS.md`](rag/AGENTS.md) 为准。
7. **导入与异常**：遵守上层 engines 红线（不反向依赖 `apps.*` / `django.*`）。

## AI 阅读与检查流程（必读）

1. **任何 engines 任务**：先读 [`engines/AGENTS.md`](../AGENTS.md)。
2. **改本包架构、目录职责、工具/提示词配置、新建 Agent 时**：再读**本文件**全文；涉及 RAG / 语音时另读对应子目录 AGENTS。
3. **即将编写或修改 `engines/agents/**` 代码时**：先读 [`.agents/rules/engines-code-style.md`](../../.agents/rules/engines-code-style.md)。
4. **只做只读分析且不改代码时**：可以不读 style rules。
5. **需要机械化风格检查时**：使用 [`.agents/skills/engines-agents-style-check/`](../../.agents/skills/engines-agents-style-check/)：
   ```text
   cd .agents/skills/engines-agents-style-check
   python -m scripts.check_engines_agents_style
   ```

## 相关路径速查

| 用途 | 路径 |
|------|------|
| 上层 engines 必读入口 | [`engines/AGENTS.md`](../AGENTS.md) |
| 规范原文（风格） | [`.agents/rules/engines-code-style.md`](../../.agents/rules/engines-code-style.md) |
| 风格检查技能 | [`.agents/skills/engines-agents-style-check/`](../../.agents/skills/engines-agents-style-check/) |
| RAG 子约束 | [`rag/AGENTS.md`](rag/AGENTS.md) |
| 语音子约束 | [`realtime_vocie/AGENTS.md`](realtime_vocie/AGENTS.md) |
| 提示词配置入口 | `role_sys_prompts.py` |
| 创建 Agent 清单 | [`../../dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md`](../../dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md) |
| OpenSpec Harness | [`../../openspec/specs/agent-harness/spec.md`](../../openspec/specs/agent-harness/spec.md) |
| 工具分配入口 | `tools_config.py` |
