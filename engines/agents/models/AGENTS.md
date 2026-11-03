# models 模块 AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../../AGENTS.md) → [`engines/agents/AGENTS.md`](../AGENTS.md) → **本文件**。本文件只写模型领域的增量规则；风格正文与检查技能仍以上层「AI 阅读与检查流程」为准，**冲突时本文件的领域规则优先**。

## 职责

`engines/agents/models/` 是**模型连接参数与模型实例的唯一归属**：读 YAML 的 `ModelConfig` 段、按 provider 造模型、维护命名模型目录、提供模型图片能力。别的模块不该知道 provider、密钥、base_url、vision / stream 这些词。

| 文件 | 职责 |
| --- | --- |
| `__init__.py` | **唯一对外门面**：只导出「取模型」与目录访问函数，包外只准 import 这一个文件 |
| `types.py` | `ModelConfig` / `RealtimeModelConfig`：不可变连接参数，无 IO、不建实例 |
| `catalog.py` | 命名目录（内置默认 + `config/data/config.yaml` 覆盖）、`get_text`/`get_realtime`/`get_embedding`、`model_supports_image`、`DeepSeekModelConfig` |
| `chat_model.py` | `ChatModelFactory`（DeepSeek / DashScope / OpenAI）+ 强制交卷关思考 |
| `realtime_model.py` | Omni 实时语音模型：**全仓唯一**构造实现 |
| `embedding_model.py` | 嵌入模型 + token 用量计量 |
| `tts_model.py` | 语音合成模型 |
| `loader.py` | 只读 `agent_config.yaml` 的 `<KEY>.ModelConfig` 段 |
| `fallback.py` | `AGENT_FALLBACK_*` → 备用聊天模型 |

## 红线（禁止）

1. **数据不进本包**：模型数据只在 `engines/agents/config/data/`（`agent_config.yaml` / `config.yaml`）。本包 MUST NOT 出现 `.yaml` 数据文件。
2. **包外只经门面**：其它模块 MUST NOT `from engines.agents.models.<子模块> import ...`，只能 `from engines.agents.models import ...`；`tests/graybox/unit/test_models_public_surface.py` 会扫出来。
3. **模型实例只在这里造**：包外 MUST NOT 直接构造 `agentscope` 的聊天 / 实时 / 嵌入 / 合成模型对象；需要一个模型就调门面。
4. **不装策略**：重试次数、退避、开关、降级（缺密钥要不要跳过）属于 `middleware/` / 调用方；本包只回答「这个模型长什么样、怎么造」。
5. **不碰 Harness 四分段**：`RoleConfig` / `ToolsConfig` / `ContextConfig` / `ReActConfig` 及其装载在 `engines/agents/config/`，不属于本包。
6. **不反向依赖**：本包 MUST NOT import `agent_builders`、`middleware`、`role_sys_prompts`，也不得 import `django` / `apps.*`。

## 职责判定表（新增代码照这张表落位）

| 代码在读写…… | 放哪 |
| --- | --- |
| `provider` / `model_name` / `api_key` / `base_url` / `vision` / `stream` / `voice` | `models/` |
| `RoleConfig` / `ToolsConfig` / `ContextConfig` / `ReActConfig` | `engines/agents/config/role_loader.py` |
| `.yaml` / `.md` 数据本身 | `engines/agents/config/data/` |
| 重试次数、退避间隔、中间件开关 | `engines/agents/middleware/` |

## 对外用法

```python
from engines.agents.models import get_chat_model, get_fallback_chat_model

model = get_chat_model("UI_EXECUTOR_ROLE_CONFIG")  # ChatModelBase
fallback = get_fallback_chat_model("UI_EXECUTOR_ROLE_CONFIG")  # ChatModelBase | None
```

其余门面：`get_realtime_model` / `get_embedding_model` / `get_tts_model` / `get_text` / `get_realtime` / `get_embedding` / `model_supports_image` / `DeepSeekModelConfig`。

## AI 阅读与检查流程

1. 任何 engines 任务先读 [`engines/AGENTS.md`](../../AGENTS.md)。
2. 改本包：再读本文与 [`engines/agents/AGENTS.md`](../AGENTS.md)「创建 Agent 统一流程」。
3. 写代码前先读 [`.agents/rules/engines-code-style.md`](../../../.agents/rules/engines-code-style.md)。
4. 注释自检：`cd .agents/skills/engines-docstring-check; python -m scripts.docstrings check`。
5. 命名 / 禁 import 自检：`cd .agents/skills/engines-agents-style-check; python -m scripts.check_engines_agents_style`。

## 相关路径速查

| 用途 | 路径 |
| --- | --- |
| 上层必读入口 | [`engines/AGENTS.md`](../../AGENTS.md) |
| agents 架构与角色创建流程 | [`engines/agents/AGENTS.md`](../AGENTS.md) |
| 风格规范正文 | [`.agents/rules/engines-code-style.md`](../../../.agents/rules/engines-code-style.md) |
| 模型数据 | `engines/agents/config/data/agent_config.yaml`、`config.yaml` |
| 门面守卫测试 | `tests/graybox/unit/test_models_public_surface.py` |
| 角色与四分段装载 | `engines/agents/config/role_loader.py` |
| 模型重试与回退 | `engines/agents/middleware/model_retry.py` |
