## Context

见 proposal.md - Why。现状与方案直接相关的事实：

- LLM 只有一处 `Agent(...)`，在 `engines/agents/agent_builders.py` 的 `AgentRoleFactory.create`。五个 `build_*` 自己 `load_role_spec`，再经旧包 `get_chat_model` 建模型。
- 语音有两处 `RealtimeAgent(...)`：`realtime_vocie_agent.py`（还带本地麦克风演示）和 `realtime_vocie/session.py`（会话里改写提示词、现场装 RAG 工具）。
- `models_new.create_model(表, 短名)` 已能按 `family` 造 chat / realtime，且不读文件、不缓存。`config.load_agent_config()` 返回整张角色表，`load_model_config()` 返回已注入密钥的模型表。
- `role_loader.load_role_spec` 仍 import 旧包 `models`，且按 key 读文件。config 层 AGENTS 已把它标为迁移项。
- workflow 设备侧传的是工厂函数，每步调用一次；用例侧经 `case_roles` 创建后再 `add_tool`。这两处是使用方，不是创建层。

## Goals / Non-Goals

**Goals:**

- assistant 与 models_new 对称：门面一个出口，schema 定形状，loader 取一条，create 分派构造。
- 聊天与 Omni 共用 `create_agent(角色表, 模型表, 角色键)`；族不对就拒绝，不猜测。
- 旧 `build_*` 与语音创建函数改为转调，调用方名字与返回类型不变。

**Non-Goals:**

- 不改 workflow 每步新建、不改 `case_roles` 运行时挂工具、不删 `agent_builders.py`。
- 不把本地麦克风演示收进 assistant。
- 不在本期把 `role_loader` 的旧包依赖清掉（它仍服务未切换的读取路径；新出口不调用它）。
- 不做「跨事件循环的模型缓存」。聊天模型只在同一进程、同一短名、同一 stream 下复用，以满足现有装配契约；换循环不复用留给后续，不把旧包的循环亲和缓存搬过来。

## Decisions

### 1. 新包 `engines/agents/assistant`，不在 `agent_builders.py` 里扩

备选是把 `create_agent` 直接写进现有工厂文件。否决：该文件已经同时做「读角色、取旧模型、映射四分段、造 Agent、兼容旧名」。再往里加语音分派，会让「只创建」和「兼容旧调用」缠在一起，也绕不开它对旧包 `models` 的 import。

新包四文件：

| 文件 | 职责 |
| --- | --- |
| `__init__.py` | 只导出 `create_agent` 与 `AgentConfigError` |
| `schema.py` | 角色节形状：模型短名、name、system_prompt、context、react；拒绝连接参数 |
| `loader.py` | 从整张角色表取一节并校验；不读文件 |
| `create.py` | 唯一出口：短名 → `create_model` → 按族造 `Agent` 或 `RealtimeAgent` |

### 2. 调用方传两张表，不在 assistant 里读配置

```
load_agent_config() + load_model_config()     # 只有 config 读文件、解密钥
        │
create_agent(角色表, 模型表, 角色键, *, toolkit, middlewares, with_tts)
        │
create_model(模型表, 短名)                     # 选模型仍由角色节决定，不由 assistant 猜
        │
Agent(...) 或 RealtimeAgent(...)
```

备选是 assistant 自己调用 `load_*`。否决：models_new 的红线就是「只有 config 读文件」。创建层若自己读，测试无法注入假表，也和「用哪个角色由 workflow 决定」相反。

`build_*` 转调时由它们负责读两张表再传入。这是兼容层的事，不是创建层的事。

### 3. 按模型族分派，不按角色键硬编码

角色节只留 `ModelConfig.model` 短名。assistant 用该短名取模型；`family == "chat"` 造 `Agent`，`family == "realtime"` 造 `RealtimeAgent`。embedding / tts 拒绝，错误带角色键与族名。

备选是在角色 YAML 增加 `kind: chat|realtime`。否决：模型表已经有 `family`，再写一份会漂移。现有六节（UI 执行/验收、用例编写/验收、Omni、知识库文字）都能由短名区分。

Omni 不并进 `Agent(...)`。AgentScope 2.0.9 的 `Agent.model` 类型是 `ChatModelBase`，语音必须是 `RealtimeAgent`。同一出口、两个构造函数，与 `create_model` 分四族同一手法。

### 4. 工具包与中间件是构造覆盖项，不是 YAML 字段

`create_agent` 接受可选 `toolkit`、`middlewares`、`with_tts`。不传时：空 `Toolkit()`，中间件走现有 `build_agent_middlewares`（备用模型本期不在新出口内派生，见风险）。`build_ui_executor` 等兼容入口继续用 `tools_config` 装好 toolkit 再传入。

备选是创建后再 `add_tool`。设备侧现在就是构造时注入，改成后挂会改变工具可见时机；产物工具的运行时 `add_tool` 留在 `case_roles`，本期不动。

### 5. 提示词解析留在转调边界，不进 assistant

`RoleConfig.system_prompt` 今天由 `role_loader` 把 token 解成 md 正文。assistant 收到的 `system_prompt` MUST 已是正文。兼容入口在传入前调用现有 `resolve_system_prompt` / `with_app_info`。这样 assistant 不读 `prompts/*.md`，符合 config「只有 config.py 读配置文件」的方向；token 解析函数本身仍在 `role_sys_prompts`，本期不搬。

### 6. 语音两处构造都转调，演示留在原文件

- `build_realtime_vocie_agent`：读两张表 → `create_agent(..., "OMNI_ROLE_CONFIG")` → 返回 `(agent, agent.model)`。本地 `run_local_s2s` 仍留在该文件，它是使用。
- `realtime_vocie/session.py`：删除内联 `RealtimeAgent(...)`。会话仍负责 RAG 开关、提示词追加和 toolkit；这些算完后传给 `create_agent`。会话循环、ready 事件、看门狗不动。

会话今天用环境变量里的 agent_name / system_prompt，与 YAML 的 `OMNI_ROLE_CONFIG` 不是同一份。转调时 MUST 把会话算好的 name、system_prompt、toolkit 作为覆盖传入，避免行为变成「只认 YAML、丢掉会话侧提示词追加」。

### 7. 旧 Factory 降为转调，不在本期删除

`AgentRoleFactory` 与五个 `build_*` 保留名字。实现改为：读表 → 解析提示词 → `create_agent`。Factory 若仍被单测直接构造（`test_agents.py`、`test_model_retry_middleware.py`），保留一个薄包装：收到已建好的 model 与四分段时，仍只调用 `Agent(...)` 的那条路径可以留在 assistant 的内部函数，避免测试为了构造一个 Agent 去读整张 YAML。

备选是立刻删 Factory。否决：OpenSpec 旧要求与多处测试直接引用它；先转调，删是下一次变更。

## 模块防火墙自检

- assistant MUST NOT import `apps.*` / `django.*` / `workflow` / `agent_builders` / `realtime_vocie`。
- assistant MUST NOT import `engines.agents.models`（旧包）。模型只经 `models_new.create_model`。
- assistant MUST NOT `import yaml`、MUST NOT 打开配置文件、MUST NOT 读环境变量取密钥。
- 新增依赖只有：`config` 的类型（调用方传入的 dict，assistant 自己不调用 `load_*`）、`models_new.create_model`、`role_types` 的 Context/ReAct 字段映射、`middleware.build_agent_middlewares`（仅默认中间件，可注入覆盖）。
- 不新增数据库写入。engines 继续不写业务库。
- 前端无改动。

## Risks / Trade-offs

- [默认中间件今天依赖旧包的 `get_fallback_chat_model`] → 本期 `create_agent` 不派生备用模型；兼容入口若需要备用模型，在转调时把已建好的中间件列表传入。新出口单测不要求备用模型。
- [会话提示词与 YAML 提示词两套来源] → 覆盖参数优先于角色节，session 转调时显式传入，并加一条单测锁定「追加后的提示词进了 RealtimeAgent」。
- [双创建路径短期并存] → 兼容入口单测改为断言「实例类型与名字不变」；另加源码/AST 断言：`Agent(` / `RealtimeAgent(` 只允许出现在 `assistant/`。
- [`role_loader` 仍依赖旧包] → 新出口不调用它，避免把旧依赖带进新包。清理留到旧包删除那次变更。
- [每次新实例，无缓存] → 与现契约一致；设备 SOP 本来就每步新实例。缓存不在本期做。

## Migration Plan

1. 落地 assistant 四文件与单测，此时尚无调用方，可独立回滚（删目录）。
2. `build_*` 改为转调；跑现有角色装配单测。失败则只回滚转调，保留新包。
3. 两处语音构造改为转调；跑语音配置与知识库会话单测。
4. 不删旧文件，不改 workflow。回滚第 3 步不影响第 2 步。

## Open Questions

无。族分派、工具包由调用方传入、会话提示词用覆盖参数，都已在上文定死；不影响后续任务拆分。
