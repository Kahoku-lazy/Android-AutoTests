# Engines 架构

> 2026-11-11。对照当前 `engines/` 代码，不沿用已过时的入口名。
> 平台总图见 [ARCH-平台架构设计.md](ARCH-平台架构设计.md)。那份文档里的 `models_new`、`prompt_config.py`、`mcp_config/` 已不是现状。

## 1. 结论

`engines/` 是平台的能力核心。它负责造模型、造智能体、跑工作流，以及设备、串口、OCR。它不写业务库，也不 import Django。

一个可运行角色 = 已创建的模型 + Harness。模型由 `engines.agents.models.create_model` 按短名创建。Harness（提示词、工具、上下文、ReAct、中间件）由 `assistant` 按角色键装上。选哪个角色由 workflow 或会话决定，不由模型层决定。

```text
backend（鉴权、任务、记账）
        |
        | 注入配置与只读协议，不把 ORM 交进来
        v
engines
  agents ── 模型 / 角色 / 工具 / 工作流 / RAG / 语音
  device ── 设备动作，入口 action
  uart_log ── 串口采集
  vision ── OCR，经 tool_ocr 延迟加载
  utils ── 文件读写
```

依赖只有一个方向：`backend → engines`。`engines` 不得反向依赖 `apps.*` 或 `django.*`。

## 2. 四个一级包

| 包 | 做什么 | 对外入口 | 不做什么 |
| --- | --- | --- | --- |
| `backend_bridge/` | 平台智能体运行时 | `workflow.sop_ui`、`workflow.cancel`、`session`、`model_billing` | 不写任务表、不持有密钥明文 |
| `device/` | Android 连接与动作 | `action.py` | 不让上层 import `device.android` |
| `uart_log/` | 串口 / TCP 日志采集 | `PortSwitch` | 不持有端口台账的最终真相 |
| `vision/` | 整图 OCR | `ocr.recognize` | 不在引擎启动时加载 cnocr |
| `utils/` | `YAMLFileIO` / `IniFileIO` | `io_files` | 不做业务校验 |

设备、串口、OCR 不直接绑到角色。它们经 `tools/tool_device.py`、`tool_serial.py`、`tool_ocr.py` 暴露，再由 `tools_config.py` 按角色节授予。

## 3. 智能体怎么装出来

```text
config.ini                         路径唯一来源
    |
config.load_agent_config()         角色表
config.load_model_config()         模型表；密钥已是 SecretKey
    |                          |
    |                          +-- model_view(表, 短名)     只查，不造、不解密
    |
    +-- models.create_model(表, 短名)                      只造，不缓存、不查询
              |
              +-- assistant.create_chat_agent              chat → Agent
              +-- assistant.create_voice_agent             realtime → RealtimeAgent
                        |
                        +-- agent_builders.build_*         聊天角色的兼容入口
                        +-- workflow / 会话                决定这次用谁
```

### 3.1 配置

`config.py` 是唯一读配置文件、唯一做密钥加解密的地方。路径只从 `config.ini` 来。`load_model_config()` 把 `api_key_env` 指向的值加密成 `SecretKey` 再放进表。缺密钥不阻断装载；真正 `reveal()` 时才报错。

`model_view.py` 按短名返回正式名、族、音色、维度、密钥变量名。就绪状态、音色白名单、计费档名走这里，不为了看一个字段去造模型。

角色数据在 `config/data/agent_config.yaml`。模型数据在 `config/data/models.yaml`。角色节只写 `model: <短名>` 和 `stream` 这类调用姿势。出现 `provider` / `model_name` / `base_url` / `api_key` 直接拒绝。

### 3.2 模型

`engines/ae_harness/agents/models.py` 是唯一的聊天模型创建出口：`create_model(短名)`。`engines/agents` 已整体退役（变更 retire-engines-agents），realtime / tts 两族随之取消，嵌入模型只由 `ae_harness/knowledge` 自建。

它不做的事：

- 不读文件，不读环境变量。
- 不做查询清单。查询在 `model_view`。
- 不做缓存。聊天模型按「短名 + stream」复用，缓存在 `assistant`。实时语音模型不复用。
- 不解析 `AGENT_FALLBACK_*`。备用模型只有调用方传入实例时才用。
- 不挂交卷装饰。强制交卷时关闭思考在 `middleware/handover.py`。

`models_new` 这个名字已经退役，目录就是 `models/`。不得恢复旧的 `get_chat_model` / `get_realtime_model` / `get_embedding_model` / `get_tts_model` / `get_fallback_chat_model`。

### 3.3 角色

`assistant` 按角色键创建，只创建不使用：不 `reply`，不跑 SOP，不跑语音会话。

| 出口 | 接受的族 | 产物 |
| --- | --- | --- |
| `create_chat_agent` | chat | 新的 `Agent` |
| `create_voice_agent` | realtime | 新的 `RealtimeAgent` |

embedding 与 tts 不经这里造智能体。嵌入给 RAG，TTS 目前没有生产调用方。

`agent_builders.build_*` 只转调聊天出口，并按角色节装工具包。`AgentRoleFactory` 只服务已经拿到聊天模型的兼容路径。每次 `build_*` 都是新的智能体，对话状态不跨任务共享。

四分段类型在 `config/role_types.py`：`RoleConfig`、`ToolsConfig`、`ContextConfig`、`ReActConfig`。装载在 `role_loader.py`，短名是否存在由 `model_view` 确认。

### 3.4 提示词与工具

提示词正文在 `config/data/prompts/*.md`。YAML 里写 token，运行时由 `role_sys_prompts.resolve_system_prompt` 解析。业务代码不得再硬编码一整段系统提示词。

工具实现在 `tools/tool_*.py`。分配只经 `tools_config.py`。当前工具：设备、串口、OCR、截图缓存、图片 base64、用例产物。技能目录在 `config/data/skills/`，本期不扩展 `ToolsConfig` 的产品语义。

## 4. 工作流怎么用角色

workflow 只编排。它不创建模型，不写提示词，不直接 import `tool_*`。

| 路径 | 用谁 | 做什么 |
| --- | --- | --- |
| `workflow/ui_auto_workflow.py` | `build_ui_executor` / verifier | 设备任务 SOP |
| `workflow/case_goal_workflow.py` | 用例编写 / 验收角色 | 用例产物流水线 |
| `workflow/single/` | 一个 `build_ui_executor()` | 单智能体 Android UI 对话；不启 SOP |
| `workflow/voice/` | 再导出语音会话 | 前后端唯一语音出口 |

`workflow/single` 不得 import `AgentSOPWorkflow`。`workflow/voice` 不得构造 `RealtimeAgent`。语音内部实现在 `realtime_vocie/`，backend 与 `knowledge_chat` 不得直接 import 那个包。

## 5. 三条运行路径

```text
设备 SOP
  backend 下发任务
    → workflow.ui_auto_workflow
    → build_ui_executor / build_ui_verifier
    → tool_device / tool_serial / tool_ocr
    → device.action / uart_log / vision.ocr
    → messaging 事件与用量
    → backend 写库，前端展示

知识库语音
  /ws/knowledge-assistant/?mode=voice
    → workflow.voice
    → realtime_vocie.session
    → create_voice_agent
    → rag.search_knowledge（当轮注入）

知识库文字
  同一条 WS，mode=text
    → knowledge_chat.session
    → build_knowledge_chat
    → 同一份 RAG 索引
    → 不装 TTS，上下文不跨连接
```

RAG 只索引 `.md` / `.txt`，索引写在配置的本地目录。检索失败返回空上下文，不中断会话。嵌入模型经 `create_model` 创建；用量回调留在 RAG 服务里，不进创建出口。

## 6. 事件、重试、计费

| 关切 | 落点 |
| --- | --- |
| 回复事件折叠、上屏 | `messaging/`，接收方协议在 `event_sink` |
| 模型重试与回退 | `middleware/model_retry.py`。未传入备用实例就不回退 |
| 强制交卷关闭思考 | `middleware/handover.py`。不包装模型，避免共享实例被叠一层 |
| DeepSeek 费用 | `messaging/billing.py`。档名从 `model_view` 取，不在模型包里 |
| 上下文窗口 | `ContextConfig` → AgentScope `ContextConfig` |

没有独立的 `memory/` 包。多轮历史只活在当前智能体或当前连接里。RAG 结果只注入当轮，不写入长期历史。

## 7. 红线

1. `engines/**` 零 `django`、零 `apps.*`、零 `backend.apps.*`。
2. 只有 `config.py` 读配置文件，只有它做加解密。明文密钥不得出现在日志、`repr` 或返回值里。
3. 模型实例只在 `models.create_model` 里构造。
4. 智能体只在 `assistant` 里构造。workflow 不旁路。
5. 工具必须 `tool_*.py`，且经 `tools_config` 分配。
6. 提示词必须经 `role_sys_prompts` + `prompts/*.md`。
7. 设备动作只经 `device.action`。OCR 必须延迟导入。
8. engines 不写业务库。任务、费用、端口台账由 backend 落库。

## 8. 和旧文档的差异

[ARCH-平台架构设计.md](ARCH-平台架构设计.md) 仍写着这些旧事实，以本文为准：

| 旧写法 | 现状 |
| --- | --- |
| `models_new` 与 `models` 并存 | 两者都已随 `engines/agents` 删除，出口是 `ae_harness/agents/models.py` 的 `create_model` |
| `prompt_config.py` | `role_sys_prompts.py` |
| `skills/`、`mcp_config/` | 技能在 `config/data/skills/`；没有 `mcp_config/` |
| 语音 pipeline / livetranslate | 已删除。语音只有 Omni |
| Django 4.2 | 后端当前钉在 Django 6.0.6 |

本文只描述 engines。改平台三层分工、HTTP 信封或进程拓扑时，仍以平台架构文档为准，并应把上表同步回去。
