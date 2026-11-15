# config AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../../AGENTS.md) → [`engines/agents/AGENTS.md`](../AGENTS.md) → **本文件**。
> 本文件写 `engines/agents/config/` 的配置读取规则：路径从哪来、谁能读文件、密钥怎么传出去。
> 代码风格正文以 [`engines-code-style.md`](../../../.agents/rules/engines-code-style.md) 为准。

## 1. 职责

`engines/agents/config/`：**配置数据的唯一入口**。谁要读配置，先来这里拿；谁要配置路径，只从 `config.ini` 拿。

| 文件 | 职责 |
|---|---|
| `config.ini` | **唯一路径源**：`[agent_config] agent_config_file_path`、`[model_config] model_config_file_path` |
| `config.py` | **唯一读文件 + 唯一加解密**：`load_agent_config` / `load_model_config`；`SecretKey` 承载密文密钥 |
| `role_types.py` | Harness 四分段类型（`RoleConfig` / `ToolsConfig` / `ContextConfig` / `ReActConfig`）；冻结 dataclass，不依赖 builders / models |
| `model_view.py` | 按短名只读查看模型规格；不造实例、不解密 |
| `role_loader.py` | 角色四分段装载（`load_role_spec` → `RoleBundle`）；短名存在性经 `model_view` 确认 |
| `log_keywords.py` | 按 SKU 做白名单与缺失降级；正文经 `config.py` 读取 |
| `__init__.py` | 包标记，无公开符号 |
| `data/` | `agent_config.yaml`（角色）、`models.yaml`（模型资产表）、`prompts/`、`app_info/`、`skills/`、`log_keywords/` |

## 2. 三条硬规则

### 2.1 路径只从 `config.ini` 来

- 任何配置文件路径，**MUST** 先在 `config.ini` 里登记，再由 `config.py` 读出来。
- 一个路径 **MUST** 只有一个常量，**MUST NOT** 出现「同一个路径两个常量」或「一个常量被赋值成另一个路径」。
- 历史教训：曾出现 `MODEL_CONFIG_FILE_PATH = AGENT_CONFIG_FILE_PATH`，导致用模型路径读到了角色配置。

### 2.2 只有 `config.py` 读文件

- 配置类文件（`agent_config.yaml` / `models.yaml` / `prompts/*.md` / `log_keywords/*.md`）**MUST** 经 `config.py` 读取。
- 其它模块 **MUST NOT** `import yaml`、**MUST NOT** `path.read_text()` 去读配置文件。
- 读文件统一走 `engines.utils.io_files`（`YAMLFileIO` / `IniFileIO`），**MUST NOT** 直接用 `open()`。

### 2.3 密钥只以 `SecretKey` 往外传

- 明文密钥 **MUST NOT** 出现在任何返回给下游的数据结构里。
- `load_model_config()` 读到表后立即：读 `api_key_env` → 加密 → 注入 `api_key: SecretKey`。
- 下游只允许调 `SecretKey.reveal()`，解密发生在 `config.py` 内部；**加解密实现 MUST NOT 外流**。
- 缺环境变量 **MUST NOT** 阻断装载：该条目的 `SecretKey` 为假值，`reveal()` 时才报错。这样只配了部分厂商密钥的环境也能装载整表。

## 3. 数据流

```
config.ini                     # 路径唯一来源
   │  IniFileIO
   ▼
config.py
   ├─ AGENT_CONFIG_PATH ─→ load_agent_config() ─→ {角色节: 四分段原始数据}
   └─ MODEL_CONFIG_PATH ─→ load_model_config() ─→ {短名: 条目 + api_key: SecretKey}
   │
   ▼
role_loader / models / agent / backend
   （只拿数据，不碰文件、不碰明文密钥）
```

## 4. 红线（禁止）

1. **禁止**在 `config.py` 之外新增「读配置路径」的常量或函数。
2. **禁止**在 `config.py` 之外 `import yaml` / `open()` / `read_text()` 读配置文件。
3. **禁止**把明文密钥写进日志、异常消息、`repr`、返回值；`SecretKey` 的 `__repr__` / `__str__` 必须打码。
4. **禁止**在配置层做业务校验：`family` / `provider` / `dimensions` 等字段归 `models.schema`，配置层只看「文件能不能读、顶层是不是映射表」。
5. **禁止**在配置层造模型、选模型、缓存实例——那是 `models`（造）和 `agent`（选 + 缓存）的事。
6. **禁止**恢复历史别名（`load_models_config`、`MODEL_CONFIG_FILE_PATH`、导入即加载的 `AGENT_CONFIG` / `MODEL_CONFIG`）。

## 5. 已知迁移项（现状 ≠ 目标）

| 位置 | 现状 | 目标 |
|---|---|---|
| `role_loader.py` | 已改：拿整表后按键取节；本期不搬家、不删除 | 保持；生产装配仍走 `assistant.loader` |
| `log_keywords.py` | 已改：正文经 `config.py`，本模块只做降级 | 保持 |
| `role_sys_prompts.py`（在上一层） | 已改：正文经 `config.py`，本模块只解析 token | 保持 |

## 6. 快速验证

```powershell
# 路径与读取
python -c "from engines.agents.config.config import AGENT_CONFIG_PATH, MODEL_CONFIG_PATH; print(AGENT_CONFIG_PATH, MODEL_CONFIG_PATH)"

# 读模型表（密钥已加密注入；缺密钥不报错）
python -c "from engines.agents.config.config import load_model_config; c = load_model_config(); print(len(c), repr(c['deepseek_flash']['api_key']))"

# 加解密往返 + 打码：repr 只有 ****，reveal 才拿回原文
python -c "from engines.agents.config.config import SecretKey, _encrypt; k = SecretKey(_encrypt('sk-demo'), env_name='DEEPSEEK_API_KEY'); print(repr(k), '|', k.reveal())"
```

## 7. 相关路径

| 用途 | 路径 |
|---|---|
| 上层 agents 约束 | [`../AGENTS.md`](../AGENTS.md) |
| 模型层（校验 + 创建） | [`../models/AGENTS.md`](../models/AGENTS.md) |
| 文件读写工具 | `engines/utils/io_files.py` |
| 风格规范 | [`.agents/rules/engines-code-style.md`](../../../.agents/rules/engines-code-style.md) |
| 注释检查 | `.agents/skills/engines-docstring-check/` |
| 风格检查 | `.agents/skills/engines-agents-style-check/` |
