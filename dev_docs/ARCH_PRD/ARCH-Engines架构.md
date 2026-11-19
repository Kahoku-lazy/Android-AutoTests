# Engines 架构

> 2026-11-18。对照当前 `engines/` 代码。`engines/agents/` 已退役，角色与流程不在 `ae_harness` 里。
> 平台总图见 [ARCH-平台架构设计.md](ARCH-平台架构设计.md)。那份文档里的 `models_new`、`prompt_config.py`、`mcp_config/` 已不是现状。

## 1. 结论

`engines/` 是平台的能力核心。它负责造模型、造智能体、跑工作流，以及设备、串口、OCR。它不写业务库，也不 import Django。

一个可运行角色由 `backend_bridge` 装配：调用方传入提示词正文和连接参数，`ae_harness.agents.create_agent` 只负责造出智能体。`ae_harness` 不保存角色、提示词或流程，也没有模型短名。

```text
backend（鉴权、任务、记账）
        |
        | 注入配置与只读协议，不把 ORM 交进来
        v
engines
  ae_harness ── 造智能体 / 工具 / 事件 / 中间件 / SOP 抽象 / 只读检索
  backend_bridge ── 用上面的原语装配平台角色与流程
  device ── 设备动作，入口 action
  uart_log ── 串口采集
  vision ── OCR，经 tool_ocr 延迟加载
  utils ── 文件读写
```

依赖只有一个方向：`backend → engines`。`engines` 不得反向依赖 `apps.*` 或 `django.*`。

## 2. 四个一级包

| 包 | 做什么 | 对外入口 | 不做什么 |
| --- | --- | --- | --- |
| `ae_harness/` | Agent 原语 | `create_agent`、`tools`、`event`、`workflow.sop` | 不定义角色、不保存提示词与流程 |
| `backend_bridge/` | 平台角色与流程装配 | `workflow.bound_sop`、`workflow.cancel`、`session`、`model_billing` | 不写任务表、不持有密钥明文 |
| `device/` | Android 连接与动作 | `action.py` | 不让上层 import `device.android` |
| `uart_log/` | 串口 / TCP 日志采集 | `PortSwitch` | 不持有端口台账的最终真相 |
| `vision/` | 整图 OCR | `ocr.recognize` | 不在引擎启动时加载 cnocr |
| `utils/` | `YAMLFileIO` / `IniFileIO` | `io_files` | 不做业务校验 |

设备、串口、OCR 不直接绑到角色。设备动作经 `ae_harness/tools/adb/` 暴露，由 `backend_bridge` 按调用方的勾选挂上。

## 3. 智能体怎么装出来

```text
运营库（提示词、厂商、密钥名、模型名、工具勾选）
    |
backend_bridge
    |-- create_agent(名称, 提示词正文, 连接参数)     ae_harness.agents
    |-- 按勾选挂 tools/<域>/                          ae_harness.tools
    |-- 挂观测 / 重试 / 预算 / 取消                    ae_harness.middleware
    '-- 名片绑定 SOP：load_spec + run_sop             ae_harness.workflow.sop
```

### 3.1 配置

`ae_harness` 不保存角色表，也没有 `models.yaml`。聊天模型的连接参数由调用方传给 `create_model`；密钥由 `models.py` 从仓库根 `.env` 再查进程环境，只记环境变量名。

平台的提示词、模型与工具勾选在运营库，运行时由 `backend_bridge` 读出后传入。

### 3.2 模型

`engines/ae_harness/agents/models.py` 是唯一的聊天模型创建出口：`create_model(provider, api_key_env, model_name, base_url)`。`engines/agents` 已整体退役，realtime / tts 两族随之取消，嵌入模型只由 `ae_harness/knowledge` 自建。

它不做的事：

- 不读角色配置，不按短名查表。
- 不缓存模型实例。
- 不解析 `AGENT_FALLBACK_*`。备用模型只有调用方传入实例时才用。
- 不挂交卷装饰。

不得恢复 `get_chat_model` / `get_realtime_model` / `get_embedding_model` / `get_tts_model` / `get_fallback_chat_model`，也不得恢复模型短名。

### 3.3 角色

角色不在 `ae_harness` 定义。`create_agent` 只收名称、提示词正文和连接参数，返回一个工具包为空的智能体。

| 装配 | 位置 | 做什么 |
| --- | --- | --- |
| 名片绑定 SOP | `backend_bridge/workflow/bound_roles.py` | 一对角色：执行侧按勾选挂工具，验收侧只留只读交集 |
| 单角色会话 | `backend_bridge/agents/ui_executor.py` | 一个执行者，挂全量设备工具 |
| 助手对话 | `backend_bridge/agents/card_agent.py` | 按名片正文和勾选挂工具 |

每次装配都是新的智能体。对话状态不跨任务共享。

### 3.4 提示词与工具

提示词正文由调用方传入，不在引擎里保存文件，也不再按 token 解析。

工具在 `ae_harness/tools/<域>/`：`adb`、`case_library`、`document`。`catalog.py` 只列名字；勾选过滤在 `backend_bridge/agents/tool_selection.py`。

## 4. 工作流怎么用角色

`ae_harness/workflow/sop/` 只编排。它不创建模型，不写提示词，不挂工具。

平台流程在 `backend_bridge/workflow/bound_sop.py`：调用方提供步骤 YAML，本函数装配两个角色后调用 `load_spec` / `run_sop`。单角色会话不走 SOP。

实时语音与 `RealtimeAgent` 已下线，没有语音工作流。

## 5. 运行路径

```text
名片绑定 SOP
  backend 下发任务（步骤 YAML + 两侧名片）
    → backend_bridge.workflow.bound_sop
    → create_agent + tools/<域>/
    → ae_harness.workflow.sop.run_sop
    → event 记录与报告
    → backend 写库，前端展示

单角色会话
  backend 打开会话
    → backend_bridge.session
    → build_ui_executor
    → 多轮 reply，跑完出报告

知识库检索
  backend/apps/knowledge_search
    → ae_harness.knowledge.KnowledgeRetriever
    → 只读命中 + 嵌入用量
    → 不造 Agent，不生成答案
```

知识库只索引 `.md` / `.txt`。检索失败降级为「检索不可用」，与「没命中」分开。嵌入模型由 `knowledge/models.py` 自建，不经聊天模型出口。

## 6. 事件、重试、计费

| 关切 | 落点 |
| --- | --- |
| 事件记录与 HTML 报告 | `ae_harness/event/` |
| 模型重试 | `ae_harness/middleware/retry.py`。只重发同一请求，不换模型 |
| 预算与取消 | `ae_harness/middleware/control.py`。`BudgetExceeded` 记中止，`RunCancelled` 记取消 |
| 费用 | `backend_bridge/model_billing/`。价目不在模型包里 |

没有独立的 `memory/` 包。多轮历史只活在当前智能体里。

## 7. 红线

1. `engines/**` 零 `django`、零 `apps.*`、零 `backend.apps.*`。
2. 明文密钥不得出现在日志、`repr` 或返回值里。只记环境变量名。
3. 聊天模型只在 `ae_harness/agents/models.py` 的 `create_model` 里构造。
4. 智能体只经 `create_agent` 构造。`backend_bridge` 不直接 `Agent(...)`。
5. 工具放 `ae_harness/tools/<域>/`，由 `catalog.py` 列出，调用方按勾选挂载。
6. 提示词由调用方传入正文。`ae_harness` 不保存提示词文件。
7. 设备动作只经 `device.action`。OCR 必须延迟导入。
8. engines 不写业务库。任务、费用、端口台账由 backend 落库。

## 8. 和旧文档的差异

[ARCH-平台架构设计.md](ARCH-平台架构设计.md) 仍写着这些旧事实，以本文为准：

| 旧写法 | 现状 |
| --- | --- |
| `models_new` 与 `models` 并存 | 两者都已随 `engines/agents` 删除，出口是 `ae_harness/agents/models.py` 的 `create_model` |
| `prompt_config.py`、`prompts/*.md`、模型短名 | 提示词与连接参数由调用方传入，不在引擎保存 |
| `skills/`、`mcp_config/` | 都已删除；工具只在 `ae_harness/tools/<域>/` |
| 语音 pipeline / livetranslate / Omni | 已删除。没有语音工作流 |
| Django 4.2 | 后端当前钉在 Django 6.0.6 |

本文只描述 engines。改平台三层分工、HTTP 信封或进程拓扑时，仍以平台架构文档为准，并应把上表同步回去。
