# ae_harness/agents · 角色创建
> 归属模块：`engines/ae_harness/agents` ｜ 类型：引擎模块开发说明
> 代码真相源：`engines/ae_harness/agents/creator.py`、`engines/ae_harness/agents/models.py`
> 上级约束：engines/AGENTS.md ｜ 模块索引：engines/AGENTS.md

## 职责

本目录负责把「模型配置 + 提示词」变成一个可直接运行的**智能体角色**。

一个角色由三样东西组成：

| 组成 | 来源 |
| --- | --- |
| 模型 | `models.py` 按调用方传入的厂商、密钥名、地址、模型名造出实例 |
| 系统提示词 | 调用方传入的正文 |
| 角色名称 | 调用方传入 |

```text
agents/
  models.py      校验连接参数 + 自己读 .env + create_model（交出密钥环境变量名）
  creator.py     create_agent → AgentBundle
```

`create_agent` 是唯一出口，返回 `AgentBundle`：`.agent` 是可运行智能体，`.api_key_env` 是本次使用的密钥环境变量名（只有名字，没有值）。

```python
from engines.ae_harness.agents.creator import create_agent

bundle = create_agent(
    "runner",
    system_prompt="你是执行者。",
    provider="openai",
    api_key_env="OPENAI_API_KEY",
    model_name="deepseek-flash",
    base_url="https://test-llm.lanjingerp.com/v1",
)
agent = bundle.agent  # 挂工具、跑任务都从这里拿
print(bundle.api_key_env)  # OPENAI_API_KEY；用量记账按这个名字归组
```

**为什么多一个 `api_key_env`，这不违反红线 2**：红线 2 禁止的是给**角色**加第四样能力（工具、记忆、**能力型**中间件、路由、编排参数）。`api_key_env` 不是能力，而是「这次用的是哪把密钥」的回执——它不改变智能体行为，只让调用方不必再读配置表。返回结构变了两段，但角色本身仍只有名称、模型、系统提示词三样。

**禁止**为了省事让 `create_agent` 返回单个 `Agent` 再让调用方自己解析密钥名——那等于把配置读取重新散到调用方。

## 红线（AI 禁止事项）

1. **禁止绕过 `create_agent` 造 Agent** —— 不得在别处直接 `Agent(...)`，不得新增第二种创建入口、注册表或工厂族。
2. **禁止给角色加第四样东西（能力型）** —— 角色只有名称、模型、系统提示词；不得往 `create_agent` 里塞工具、记忆、**能力型中间件**、角色表、路由或编排参数。

   **中间件准入分三类**，每类都有明确条款（详见 [`ae_harness_middleware_admission.md`](../ae_harness_middleware/ae_harness_middleware_admission.md)）：

| 类别 | 允许做什么 | 判据 |
| --- | --- | --- |
| 只读观测 | 看、记录、采样 | 去掉它，运行结果一模一样 |
| 可靠性 | 失败时重试**同一动作** | 成功路径的调用次数与参数不变 |
| 运行控制 | 按上限或外部信号**提前中止** | 只会更早结束，不会多做一件事 |

三类都经创建时的显式入参传入（`observers=[...]`），默认一个都不挂。**能力型中间件（改变行为、扩展能力）一律禁止**，不论包装成什么名字。
3. **禁止在本目录读取或保存角色提示词文件** —— `create_agent` 只收调用方传入的正文。聊天模型没有 `models.yaml`，连接参数由调用方传入。知识库的向量模型与库列表由调用方传入，不在本目录读取。
4. **禁止 `creator.py` 自己构造模型客户端** —— 必须经 `models.create_model`，不得直接实例化 `DeepSeekChatModel` 之类的类。
5. **禁止在 `create_agent` 里调用 `reply` / `reply_stream`** —— 只创建，不运行；何时开始对话由调用方决定。
6. **禁止引入语音、TTS** —— 本目录只服务 chat 角色；遇到这类需求先上报，不要自行扩展。**知识库检索**由调用方把根级 `knowledge/` 的工具挂到角色上（工具不算角色第四要素），本目录**不感知、不 import**。
7. **禁止把连接参数收成短名或配置文件** —— `name` 只收角色名称、`system_prompt` 只收提示词正文；模型必须由调用方显式传入 `provider`、`api_key_env`、`model_name`、`base_url`。不得恢复模型短名，不得让这四个参数兼容模型实例，不得再按文件名读提示词。
8. **禁止在本目录新增第二套配置来源** —— 不得再加一个 `settings.py`、第二个 yaml 或另一个提示词目录。

## 观测中间件准入清单

背景：AgentScope 的中间件只能在 `Agent(...)` 构造时传入，而 `create_agent` 是唯一创建出口，所以「挂观测中间件」必然要经过本目录。为守住「角色只有三样东西」，边界按下面写死。

### 允许（只读观测）

1. **读取 hook 入参并计数、计时、采样**：模型名、token 数、消息内容、最终 system prompt、压缩前后的阈值与比例、工具名与执行结果。
2. **通过注入的 `emit(record)` 回调投递记录**。投到哪、如何落盘、如何渲染，全由事件层决定；中间件不认识事件层，也不持有其容器。
3. **对变换式 hook 原样透传**：读到值后一字不改地返回。

### 禁止（按 hook 逐条）

| hook | 形态 | 观测中间件可以做什么 | 绝对禁止 |
| --- | --- | --- | --- |
| `on_reply` | Onion | 包裹一次回复，读入参/出参 | 改输入或输出、吞异常、跳过 `next_handler` |
| `on_reasoning` | Onion | 包裹一轮推理，计时 | 改输入、改返回、跳过 `next_handler` |
| `on_acting` | Onion | 观察一次工具执行，记耗时与结果状态 | 改工具入参、改工具结果、跳过执行 |
| `on_model_call` | Onion | 观测请求与响应，读 token 与模型名；`capture_messages=True` 时读消息正文 | 改写 `kwargs`（含 `extra_body` / `tool_choice`）、换模型、跳过调用 |
| `on_compress_context` | Onion | 观测是否压缩、压缩比例、注入的指令 | 改变压缩结果、改上下文 |
| `on_system_prompt` | Transformer | **读到最终提示词后原样返回** | 改一个字符、注入任何指令（改了就是能力型） |
| `on_check_permission` | Onion | 只读观测权限判定 | 改动判定结果（安全红线） |
| `list_tools` | Tool source | —— | **完全禁止**：它直接扩展能力 |

### 通用禁止

1. **不得吞异常**：捕获后必须 `raise` 或交给下游，不得静默 `pass`。
2. **不得写状态**：`agent.state`、`tool_context`、上下文消息一律只读。
3. **不得做控制类行为**：重试、回退、缓存、并发控制、预算熔断、跳过步骤。
4. **不得触碰外部资源**：不发网络请求、不读配置或密钥、不写文件（落盘归事件层）。
5. **不得改变控制流**：提前 `return`、条件性跳过 `next_handler`、替换返回值。

### 装配方式

- 只允许在创建智能体时经**显式观测入参**传入：`create_agent(..., observers=[...])`。该入参与能力型中间件分开命名，**禁止**复用同一个参数名、禁止把观测中间件伪装成能力型中间件。
- `create_agent` 只把 `observers` 透传给 `Agent(middlewares=...)`；本目录**不 import** `middleware`，不认识观测实现。
- 一次运行**只挂一个**观测中间件；SOP 里两个角色可共用同一个实例，观测记录带 agent 名以区分归属。
