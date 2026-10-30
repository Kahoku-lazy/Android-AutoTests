# GUIDE — 创建 Agent 清单

> 目标：让 AI / 开发者按 **Model + Harness → 角色** 新增能力，而不是把逻辑写进 Django View 或前端。  
> 必读：根 [`AGENTS.md`](../../AGENTS.md)「平台架构定位」· [`engines/AGENTS.md`](../../engines/AGENTS.md) · [`engines/agents/AGENTS.md`](../../engines/agents/AGENTS.md)（含「创建 Agent 统一流程」）· 风格 [`.agents/rules/engines-code-style.md`](../../.agents/rules/engines-code-style.md) · OpenSpec [`agent-harness`](../../openspec/specs/agent-harness/spec.md)

## 0. 先判定落点

| 你想做的事 | 落点 | 不要做的事 |
| --- | --- | --- |
| 新智能体角色（推理+工具） | `engines/agents/`（本清单） | 在 `backend/apps/*/views` 里写 SOP/工具调用 |
| 只改任务下发/密钥/落库展示 | `backend/apps/ai_assistant`、`task_list` 等 | 在 engines 里写 Django ORM |
| 新设备/串口/OCR 原子能力 | `engines/device` / `uart_log` / `vision`，再经 `tool_*.py` 暴露 | 上层直接 import uiautomator2/airtest |
| 仅 UI 文案或列表展示 | `frontend/` | 在前端拼模型密钥或直连设备 |

**公式：** `角色 = Model（provider/模型名/密钥来源）+ Harness（提示词 + 工具/技能/知识/上下文）`，经 `AgentRoleFactory`（LLM）或 `realtime_vocie_agent`（Voice）装配。

## 1. 最小必做清单（代码角色）

对照现有：`agent_builders.py`（UI / 用例 `build_*`）、`realtime_vocie_agent.py`（Omni）。

1. **模型**  
   - 在 `config/data/agent_config.yaml` 增加角色节的 `ModelConfig`（及四分段）。  
   - 经 `engines.agents.config.models.load_role_config` / `ChatModelFactory` 装载；密钥只写环境变量名。

2. **提示词**  
   - 新增 `engines/agents/config/data/prompts/<TOKEN>.md`。  
   - YAML `RoleConfig.system_prompt` 填 token；在 `role_sys_prompts.py` 登记类方法或常量（若需模块级导出）。  
   - **禁止**在 View / 其它包硬编码整段 system prompt；**禁止**再引入已删的 `prompts/` 包或 `prompt_config.py`。

3. **工具（若需要）**  
   - 实现放 `engines/agents/tools/tool_<领域>.py`（命名必须 `tool_*.py`）。  
   - 在 `tools_config.py` 增加 `build_<角色>_toolkit()`（或扩展现有 build）。  
   - **禁止**在 builder 里直接 `from .tools.tool_xxx import ...` 绑业务工具绕过 `tools_config`。

4. **技能（若需要）**  
   - 技能目录放 `config/data/skills/`，挂到 `tools_config` 的 `skill_dirs`。

5. **角色装配**  
   - LLM：在 `agent_builders.py`（或同包 builder）用 `AgentRoleFactory(...).create()`，提供 `build_xxx() -> Agent`，**每次新实例**。  
   - Voice：扩展 `realtime_vocie_agent` + `realtime_vocie` 会话；勿恢复 livetranslate/pipeline。  
   - **禁止**再使用已删除的 `role/` 包、`BaseRole`、`case_roles.py`。

6. **工作流（若走 SOP）**  
   - 步骤编排放 `workflow/`；**不在 workflow 里**创建角色或旁路绑工具/提示词。

7. **知识（若需要 RAG）**  
   - 走 `rag/`，遵守其 AGENTS；结果只注入当轮上下文。

8. **记忆与上下文**  
   - 优先复用 messaging / Omni session；不要平行再造一套写业务库的历史存储。

## 2. 平台通道清单（要可配置、可计量、可展示时）

1. `backend/apps/ai_assistant`：智能体与 `route_configs`（密钥 Fernet）。  
2. 任务路径：`task_list` 提交 → 解密配置 → 调用 engines 入口 → 事件/用量入库。  
3. 前端：`ai-assistant` / `task-list` 展示；**不**在前端保存明文长期密钥。  
4. engines **不**直接写业务库。

## 3. 自检（做完必须跑）

```text
cd .agents/skills/engines-agents-style-check
python -m scripts.check_engines_agents_style

python -m utils.check_gates --only engines-agents-style
# 或
python run.py check
```

人工核对：

- [ ] 提示词只经 `role_sys_prompts` + `config/data/prompts`  
- [ ] 模型只经 `config/models` + `agent_config.yaml`  
- [ ] 工具只经 `tools_config` + `tool_*.py`  
- [ ] LLM 经 `AgentRoleFactory` / `build_*`；Voice 经 `realtime_vocie_agent`  
- [ ] 无 `import apps` / `django` 出现在本次 engines 改动  
- [ ] 未在 View 内嵌 SOP 循环或设备操作  

## 4. 反模式（看到就停）

- 在 DRF View / `api.py` 里直接 `Agent(` 或调用 uiautomator2  
- 新工具文件命名 `test_*.py` 或放在 `backend/`  
- 复制提示词到 frontend / backend「方便改」  
- 复活 `role/`、`prompt_config`、`prompts/*_prompt.py`、BaseRole  
- 为图省事 `git add -A` 把 temps / 密钥加进提交  

## 5. 参考实现

| 场景 | 参考 |
| --- | --- |
| 设备执行 + 验收 | `agent_builders.build_ui_executor` / `build_ui_verifier` + `tools_config` |
| 用例规划/编写/验收 | `agent_builders.build_case_*` |
| Omni 语音 | `realtime_vocie_agent` + `realtime_vocie` |
| 提示词登记 | `role_sys_prompts.py` + `config/data/prompts/*.md` |
| 模型登记 | `config/models.py` + `config/data/agent_config.yaml` |
| 工具登记 | `tools_config.py` + `tools/tool_*.py` |
