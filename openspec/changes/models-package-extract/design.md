## Context

现状（动机见 proposal.md - Why）：

- `engines/agents/config/models.py` 共 803 行，混合四类内容：模型数据类型（`ModelConfig` / `RealtimeModelConfig` / `*ModelReady`）、模型工厂（`ChatModelFactory` + 强制交卷关思考）、角色四分段装载（`_merge_dataclass` / `load_role_config` / 8 个 `*_role_config`）、命名模型目录（`TEXT_MODELS` 等）。
- 模型实例构造点 5 处：`agent_builders`（主模型 + 备用模型）、`realtime_vocie/config.create_realtime_model`、`rag/service._UsageEmbeddingModel`、`middleware/tts.build_tts_middleware`，以及 `config/models.omni_realtime_model`（与 `realtime_vocie` 那处**并列重复**）。
- 反向知识污染：`role_sys_prompts` 持有 `DEEPSEEK_MODELS` / `model_supports_image`；`middleware/model_retry.RetrySettings` 持有 `AGENT_FALLBACK_*` 四个连接参数。
- 导入方向：`config.models` 为了装角色而 import `role_sys_prompts`（`resolve_system_prompt` / `with_app_info`），于是「模型模块」依赖「提示词模块」。
- 已有约束：`engines/**` 零 `django` / `apps.*`；模型数据只在 `config/data/`；agentscope 固定 2.0.9，模型类 API 不自行改写。`engines/agents/models/` 目录已存在且为空（未入库）。

## Goals / Non-Goals

**Goals:**

- 模型代码（类型、目录、工厂、装载、备用模型）全部落在 `engines/agents/models/`，包外只经包入口取实例。
- 数据零迁移：`config/data/agent_config.yaml` 与 `config/data/config.yaml` 的结构、键名、位置不变。
- 消除 Omni 双实现；聊天 / 实时 / 嵌入 / 合成四类模型的构造各只有一处。
- 拆完后 `models` 包不依赖 `role_sys_prompts`、不依赖 `agent_builders`，可单独 `import`。

**Non-Goals:**

- 不新增 provider、不改模型选型、不改 `agent_config.yaml` 的字段与角色清单。
- 不动中间件顺序、开关语义、`max_iters`、SOP 与事件/计费链路。
- 不把 `RoleConfig` / `ToolsConfig` / `ContextConfig` / `ReActConfig` 挪进 `models`（它们属 Harness）。
- 不重构 `config/config.py`（YAML 读取）与 `utils.io_files`。
- 不改 backend / 前端（`backend/apps/ai_assistant/provider_registry.py` 只有一句注释要跟）。

## Decisions

### D1 包结构：按「一类模型一个文件」

```
engines/agents/models/
├── __init__.py        # 唯一门面：取模型函数 + 目录访问 + __all__ 白名单
├── types.py           # ModelConfig / RealtimeModelConfig（纯数据类，无 IO、不建实例）
├── catalog.py         # *ModelReady 目录项（含建模型便捷方法）+ 内置目录/YAML 覆盖 + get_text/get_realtime/get_embedding + model_supports_image + DeepSeekModelConfig
├── chat_model.py      # ChatModelFactory + apply_forced_handover_kwargs / bind_forced_handover
├── realtime_model.py  # Omni 实时模型（合并两处重复实现）
├── embedding_model.py # 嵌入模型 + 用量计量子类
├── tts_model.py       # 语音合成模型
├── loader.py          # 只读 <KEY>.ModelConfig 段 → ModelConfig / RealtimeModelConfig
├── fallback.py        # AGENT_FALLBACK_* → 备用聊天模型
└── AGENTS.md          # 本包红线与判定规则
```

理由：现状 803 行里四类内容互不相关；按「一类模型一个文件 + 装载/备用各一」切，改 TTS 不会碰到 `agent_config` 装载。**备选**：单文件 `models/__init__.py` 保持现状搬移 → 只换了位置，没解决职责混杂。

### D2 门面就是包根 `__init__.py`

`__init__.py` 只做「读参数 → 调子模块 → 返回实例」，并显式维护 `__all__`。包外 MUST 只 `from engines.agents.models import ...`。**备选**：`models/api.py` / `models/facade.py` → 用户要求「一个对外的文件」，包根最直观，且 `import engines.agents.models` 天然可用；`api.py` 会多一层无意义跳转。

门面签名：

| 函数 | 入参 | 返回 |
| --- | --- | --- |
| `get_chat_model(role_key)` | `agent_config.yaml` 顶层键 | `ChatModelBase` |
| `get_fallback_chat_model(role_key)` | 同上 | `ChatModelBase \| None` |
| `get_realtime_model(api_key, model_name=None, parameters=None)` | 密钥 + 可选覆盖 | `DashScopeRealtimeModel` |
| `get_embedding_model(api_key, name="text_embedding_v4", usage_sink=None)` | 密钥 + 目录名 + 用量回调 | 嵌入模型 |
| `get_tts_model(api_key=None, model_name=None, voice=None)` | 可选覆盖 | `DashScopeTTSModel` |
| `get_text/get_realtime/get_embedding(name)` | 目录名 | `*ModelReady` |
| `model_supports_image(provider, model_name)` | provider + 模型名 | `bool \| None` |

### D3 角色键取模型，而不是保留 8 个角色函数

`get_chat_model("UI_EXECUTOR_ROLE_CONFIG")` 直接对应 YAML 顶层键，一个函数覆盖执行 / 验收 / 用例编写 / Goal 变体 / Omni 角色。`executor_model()` / `verifier_model()` 这类名字随角色增减而膨胀，退役。**备选**：给每个角色一个门面函数 → 8 个近乎相同的函数，且新增角色要改 models 包。

### D4 角色装载改返回 `RoleBundle`，不再回传模型配置

`config/role_loader.py` 提供 `load_role_spec(role_key) -> RoleBundle`（`frozen dataclass`：`role_key` / `role` / `tools` / `context` / `react`）。`Toolkit()` 默认、`app_info` 追加、空节报错等现有语义逐条保留；`_merge_dataclass` / `_is_empty_section` 随之搬过去。旧名 `load_role_config`、`ui_*_role_config`、`case_*_role_config` 与 `load_role_spec` 别名一并退役。**备选**：保留 5 元组兼容 → 装配层仍持有 `ModelConfig`，与本次目标冲突。

### D5 备用模型参数归 models，重试策略留中间件

`models/fallback.py` 读 `AGENT_FALLBACK_MODEL` / `_PROVIDER` / `_BASE_URL` / `_API_KEY`，结合该角色 `ModelConfig` 的 vision / stream / 默认密钥与地址，返回已建好的备用模型。`RetrySettings` 只保留 attempts / base_delay / max_delay / enabled；`build_agent_middlewares(fallback_model=...)` 契约不变。**备选**：env 留在 `RetrySettings`、构造时调 models → 两个模块重复读同一批变量，且中间件仍摸连接参数。

### D6 嵌入用量计量留在 models

`embedding_model.py` 提供 `get_embedding_model(..., usage_sink=...)`，内部子类只覆写 `__call__` 记录 token。RAG 只传回调，不再继承 `DashScopeEmbeddingModel`。**备选**：留在 `rag/service.py` → 调用方仍要懂模型类，与本变更目标冲突。

### D7 TTS 构造搬走，中间件只留开关与降级

`get_tts_model()` 负责缺依赖 / 缺密钥之外的构造；`build_tts_middleware` 保留「开关未开 → None」「缺 `DASHSCOPE_API_KEY` → 警告 + None」「缺 TTS 依赖 → 警告 + None」三条现有语义，只在能构造时调门面。

### D8 目录覆盖文件的落点

现状 `_CONFIG_YAML = Path(__file__).with_name("config.yaml")` 指向 `engines/agents/config/config.yaml`（不存在，故一直用内置默认）。`catalog.py` 搬到 `models/` 后，`with_name` 会指向 `models/config.yaml`——那正是 spec 禁止的「模型数据进 models 包」。改为显式指向 `engines/agents/config/data/config.yaml`（同样不存在，行为一致），并在注释写明「数据归 config」。

### D9 依赖方向（拆完必须成立）

```
agent_builders / realtime_vocie / rag / middleware.tts / messaging.billing
        └──→ engines.agents.models（仅包入口）
                    ├──→ types / catalog（无本地依赖）
                    ├──→ chat_model / realtime_model / embedding_model / tts_model
                    └──→ loader ──→ config.config（只读 YAML 数据）
config.role_loader ──→ role_sys_prompts（提示词解析），不再 import models
```

`models` 不 import `role_sys_prompts`、不 import `agent_builders`、不 import `middleware`；`config` 也不 import `models`。切断了现存 `config.models → role_sys_prompts` 的耦合。

### D10 门面守卫用测试，不用 linter 规则

新增 `tests/graybox/unit/test_models_public_surface.py`：AST 扫描 `engines/**/*.py`（跳过 `engines/agents/models/**`），断言无 `from engines.agents.models.<子模块> import`；再扫 `engines/`（跳过 models 包）断言无 `agentscope.model|embedding|tts|realtime` 模型类构造。**备选**：ruff `banned-api` → 需要为四个前缀维护配置、报错信息对读者不友好、且挡不住「以字符串反射构造」。

### D11 报错语义保持

条件与异常类型一律不动：缺环境变量 / 缺 YAML 节 / 未知 provider / 缺 `agentscope[realtime]` / 未知目录名（`ValueError` / `RuntimeError` / `KeyError`）。仅文案里的模块路径随新落点调整。

## 模块防火墙自检

- 跨 App import：无新增。`engines/**` 仍零 `django` / `apps.*`（本变更不引入任何 DB 或业务层依赖）。
- 新增跨模块依赖只有两条，都是单向且只读：`models.loader → config.config`（读 YAML 数据）、`realtime_vocie → models`（原已依赖 `config.models`）。engines 内无 Django app，故不存在「必须走 api.py」的写入路径。
- 三处写入边界不触碰：不写数据库、不写 `data/rag_index`、不改 `config/data/**` 内容。
- 工具与提示词入口不动：`tools_config.py` / `role_sys_prompts.py` 的职责边界保持（后者只减去模型元数据）。
- 不新增自定义异常类；不新增 `tool_*.py`。

## Risks / Trade-offs

- [一次性改 8 处调用点 + 6 个测试文件，容易漏] → 每步落地后 `rg 'config\.models'`、`rg 'role_config\(\)'` 全仓归零；配合单测与真机冒烟。
- [门面 API 变更影响未知调用方] → 已全仓 grep：取模型的只有 `agent_builders` / `realtime_vocie*` / `rag` / `middleware/tts` / `billing` 与 6 个测试，workflow 不直接取模型。
- [拆分过程中出现循环导入] → 包内禁止 import `agent_builders` / `middleware` / `role_sys_prompts`；每步跑 `python -c "import engines.agents.models"`，并在最后跑装配相关单测。
- [`AGENT_FALLBACK_*` 解析搬家导致行为漂移] → 变量名、默认值、「未配置返回 None」语义逐条对齐；`test_model_retry_middleware.py` 的 4 条环境变量断言迁到 models 侧并保留。
- [TTS / 嵌入搬走后缺依赖、缺密钥的降级路径变化] → 三条 TTS 降级语义逐条保留；嵌入用量回调为 None 时不上报，保持现状。
- [错误文案变化被误判为回归] → 异常类型不变；需要文案的地方先搜测试断言再改。
- [门面守卫测试过严，误伤合法内部导入] → 只拦「包外导入子模块」，`engines/agents/models/**` 内部自由 import。

## Migration Plan

无数据迁移、无部署顺序要求（单进程内一次性替换）。按 tasks.md 的 8 步提交，每步都能独立 `import` 且既有测试通过；任一步出问题可直接 revert 该步提交，改动集中在 `engines/agents/`。

## Open Questions

- `DeepSeekModelConfig`（计费档名 `FLASH` / `PRO` 的兼容层）是否在后续变更里退役、改用 `catalog.get_text("deepseek_flash").model_name`？本次保留并随 `catalog` 迁入 models，避免同时改计费链路。
