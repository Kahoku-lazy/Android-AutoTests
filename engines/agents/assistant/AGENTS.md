# assistant AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../../AGENTS.md) → [`engines/agents/AGENTS.md`](../AGENTS.md) → **本文件**。
> 本文件只写增量：智能体创建层的两个出口、红线，以及它和 `agent_builders` / `models` 的关系。

## 1. 定位

本包只做一件事：**按角色键把一条角色配置变成智能体实例**。选哪个角色由 workflow / 会话决定。

```
config.load_agent_config() + load_model_config()   # 唯一读文件 + 唯一加解密
   │  两张表
   ▼
create_chat_agent(角色表, 模型表, 角色键)         # 只接受 chat → Agent
create_voice_agent(角色表, 模型表, 角色键)        # 只接受 realtime → RealtimeAgent
   │  内部：短名 → models.create_model
   ▼
workflow 只用聊天出口；语音会话只用语音出口
```

`models` 给本包提供模型；本包给使用方提供智能体。两层都不决定「这次用谁」。TTS 与嵌入不进本包。

## 2. 文件与入口

| 层 | 文件 | 职责 |
| --- | --- | --- |
| 门面 | `__init__.py` | 只导出 `create_chat_agent`、`create_voice_agent` 和 `AgentConfigError` |
| 出口 | `create.py` | 聊天出口只造 `Agent`；语音出口只造 `RealtimeAgent`；族不对即拒绝 |
| 成对装配 | `case_roles.py` | 用例编写/验收一次装配；根上 `engines.agents.case_roles` 只再导出 |
| 校验 | `loader.py` | 内部：按角色键取节 |
| 形状 | `schema.py` | 角色节形状；拒绝连接参数 |

## 3. 红线

1. **不读文件、不读环境变量** —— 两张表由调用方传入。MUST NOT `import yaml`。
2. **模型只经创建出口** —— MUST `from engines.agents.models import create_model`。MUST NOT import `engines.agents.models` 的子模块，也 MUST NOT 自己构造模型类。
3. **两个出口，不按实例类型分支** —— 包外只允许 `create_chat_agent` 与 `create_voice_agent`。聊天出口拒绝 realtime / embedding / tts。语音出口拒绝非 realtime，并拒绝 context、react、中间件和 stream。`Agent(` / `RealtimeAgent(` 只允许出现在本包。TTS 与嵌入不经本包创建智能体。
4. **只创建不使用** —— MUST NOT 调用 `reply` / `reply_stream`，MUST NOT 启动 SOP 或语音会话。
5. **不反向依赖** —— MUST NOT import `agent_builders` / `workflow` / `realtime_vocie` / `apps.*` / `django.*`。
6. **智能体不缓存，聊天模型按短名复用** —— 每次调用返回新的 Agent。同一进程、同一短名、同一 stream 的聊天模型复用同一实例，避免同一步里多个角色各开一个客户端。实时语音模型不复用。
7. **工具包不硬编码** —— 空工具节就是空包；设备 / 产物 / RAG 工具由调用方传入。

## 4. 与旧入口

`agent_builders.build_*` 只转调 `create_chat_agent`。`realtime_vocie_agent.build_realtime_vocie_agent` 与语音会话只转调 `create_voice_agent`。会话侧的名字、追加提示词、RAG 工具包用语音出口的覆盖参数传入，不在会话里再构造 `RealtimeAgent`。
