# engines/agents AGENTS.md

## 设计初衷

本包要驾驭 AI，不是把模型调用散落在业务里。做法是两步：先按任务需要创建 Agent 角色，再用特定工作流编排这些角色，让它们按既定分工协作，完成指定任务。

角色是可替换的执行单元：一个角色 = 选定的 Model + 跑起来所需的 Harness（提示词、工具、上下文、中间件）。工作流不另造角色，只决定这一次由谁做、按什么顺序做、做到什么算完成。

| 现有协作 | 角色 | 工作流怎么驾驭 |
| --- | --- | --- |
| 设备 SOP | 执行者动手，验收者核对 | 每步新建一对，跨步不继承上下文；验收不通过就在本步内重试 |
| 用例编写 | 编写者增量写产物，验收者核对事实 | 一条目标流水线跑完；有确定性问题时即使验收通过也不放行 |
| 单智能体 | 只有执行者 | 一次连接复用一个实例，不调用 SOP，不建第二个角色 |
| 知识助手 | 语音角色或文字角色 | 两条会话不共享上下文；检索走同一份知识库 |

新增能力先问「需要哪个角色、进哪条工作流」，再写代码。禁止在 View、workflow 或会话里旁路造模型、写提示词、绑工具。

## 编排怎么实现

编排不是 workflow 里再写一套角色。它是一条单向链：config 提供数据，model 变成实例，agent 变成可运行角色，workflow 只消费这个角色。

```text
config/data
  │  models.yaml + agent_config.yaml + prompts/
  ▼
config.py                      只读文件，密钥加密成 SecretKey
  │  两张表
  ├─ model_view                只看规格，不造实例
  ▼
models.create_model            按 family 造 chat / realtime / embedding / tts
  │  模型实例，不带角色
  ▼
assistant                      create_chat_agent / create_voice_agent，只创建不使用
  │  未传中间件时，聊天角色挂 middleware：事件、交卷、重试
  ▼
agent_builders.build_*         读表、解析提示词、按模块装工具，然后转调聊天出口
  │  每次返回新的 Agent
  ▼
workflow                       只拿工厂或已装配角色，决定顺序、重试和完成条件
```

四层各做一件事：

| 层 | 做 | 不做 |
| --- | --- | --- |
| config | 读表、读正文、加密密钥、提供只读规格 | 不造模型，不选这次用谁 |
| model | 按短名和 family 造实例 | 不读文件，不做缓存，不挂工具 |
| agent | 把模型、提示词、工具、中间件装成角色 | 不跑 SOP，不决定步骤顺序 |
| workflow | 选择角色、安排协作、判定完成 | 不读配置，不造模型，不绑工具 |

workflow 编排角色的方式只有两种，都不再往回碰 config 和 model：

1. **要工厂，不拿长生命周期实例。** 设备 SOP 收到 `build_executor` 和 `build_verifier`。每一步调用一次工厂，得到一对新实例；这一步的上下文不带进下一步。验收不通过时，本步复用这对实例重试，次数由工作流控制。
2. **要一次运行的已装配角色。** 用例编写先由 `assistant/case_roles.py` 把编写者和验收者装好并挂上产物工具，再交给目标流水线。编写者在这一次运行内保留上下文，验收者按流水线重置。单智能体和知识会话同样只复用本次连接里的一个角色。

所以「编排 Agent」的含义是：工作流通过 `build_*` 或成对装配拿到角色，再用步骤、验收、重试和完成条件约束它们。换模型改 `models.yaml`，换角色行为改提示词和工具分配，换协作方式只改 workflow。三处不互相抄实现。

## 红线（禁止）

1. **禁止**跳过本文件直接改本包架构、目录职责或工具/提示词配置方式。
2. **工具**：必须放在 `tools/`，文件名 `tool_xxx.py`；**必须**经 `tools_config.py` 分配。分配模块不放进 `tools/`。**禁止**业务代码直接 `import` 绑工具。
3. **提示词**：必须经 `role_sys_prompts.py` + `config/data/prompts/*.md`；禁止旁路硬编码。
4. **角色**：新建 LLM 角色经 `assistant.create_chat_agent`（`build_*` 只转调）；语音经 `assistant.create_voice_agent`；**禁止**恢复已删除的 `role/` 包或 `BaseRole` 旁路。
5. **workflow**：禁止在 `workflow/` 创建角色、配置提示词或绑定工具。
6. **RAG 路径与密钥**：以 [`rag/AGENTS.md`](rag/AGENTS.md) 为准。
7. **导入与异常**：遵守上层 engines 红线（不反向依赖 `apps.*` / `django.*`）。
