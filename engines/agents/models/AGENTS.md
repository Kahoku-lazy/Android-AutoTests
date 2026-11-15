# models AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../../AGENTS.md) → [`engines/agents/AGENTS.md`](../AGENTS.md) → **本文件**。
> 本文件只写增量：模型创建层的唯一出口与红线。查规格不在本包，见 `config/model_view.py`。

## 1. 定位

模型层只做一件事：**按短名把一条模型配置变成模型实例**。选哪个模型由 agent 决定。

```
config.ini                            # 唯一路径源
   │
config/config.py::load_model_config() # 唯一读文件 + 唯一加解密；密钥以 SecretKey 注入条目
   │  整张表 {短名: 条目}
   ▼
models.create_model(表, 短名)          # 唯一出口：按 family 校验 → 分派构造
   │  模型实例
   ▼
agent                                 # 选模型、拿缓存、调用模型
```

本包就是模型创建层。查规格不在这里，走 `config.model_view`。

## 2. 文件与入口

| 层 | 文件 | 职责 |
|---|---|---|
| 门面 | `__init__.py` | 只导出 `create_model`（和错误类型 `ModelConfigError`） |
| 出口 | `create.py` | `create_model(表, 短名)`：按 `family` 分派四族构造 |
| 校验 | `loader.py` | 内部：按短名取条目，按 `family` 选校验类 |
| 形状 | `schema.py` | 三个参数类（字段声明即校验）+ 跨字段规则 |

语音两族（`realtime` / `tts`）共用一个参数类 `RealtimeModelSchema`，`create` 按 `family` 再分。

## 3. 红线

1. **只有 config.py 读文件** —— 本包 MUST NOT `import yaml`、MUST NOT 打开文件、MUST NOT 出现 `.yaml` 数据文件；表由 `config.load_model_config()` 传入。
2. **不读环境变量、不碰加解密** —— 密钥由 config 加密后注入条目的 `api_key`（`SecretKey`），本包只调 `reveal()`。
3. **只有一个出口** —— 包外只允许 `create_model`；参数对象、parse、四族构造都是内部实现。
4. **不做缓存/重试** —— 归 agent 层；每次 `create_model` 都返回新实例。
5. **不做查询清单** —— `capabilities` / `describe_model` / `available_models` 不在本包。
6. **缺密钥不阻断装载** —— config 装载整张表时不因某个环境变量没配而失败；该条目的 `SecretKey` 为假值，`create_model` 调 `reveal()` 时才报 `ModelConfigError`（消息带模型名与环境变量名）。这样只有 DeepSeek 密钥的环境也能装载整表、照常用 DeepSeek 模型。
7. **不恢复旧五入口** —— MUST NOT 恢复 `get_chat_model` / `get_realtime_model` / `get_embedding_model` / `get_tts_model` / `get_fallback_chat_model`。包外只允许 `create_model`。
8. **不反向依赖** —— MUST NOT import `agent_builders` / `middleware` / `role_sys_prompts` / `apps.*` / `django.*`。

## 4. 与已删除旧实现的差异

| 已删除的五入口实现 | 本包 |
|---|---|
| 自己读表、读环境变量 | 由 `config.load_model_config()` 传入，密钥已加密 |
| 5 个取模型入口 + 查询面 | 1 个 `create_model`；查询在 `config.model_view` |
| 实例缓存、备用模型、交卷装饰 | 不在本包。缓存在 assistant，交卷在 middleware |
| `ProviderAdapter` 注册表 | 无；provider 用 `Literal` 收口 |

## 5. 迁移结果

1. 造实例只经 `create_model`。聊天缓存在 `assistant`，不在本包。
2. 查规格只经 `config.model_view`。角色引用在 `config.role_loader`。
3. 嵌入用量由 RAG 服务在创建后记录。交卷关思考在 `middleware.handover`。
4. 备用模型不由本包解析；未传入实例就不回退。
5. 包名已从 `models_new` 改为 `models`。不得恢复五入口门面。

## 6. 验证

```bash
# 功能联调（不写测试前先用这个）
python -c "from engines.agents.config.config import load_model_config; \
from engines.agents.models import create_model; \
c = load_model_config(); print(type(create_model(c, 'deepseek_flash')).__name__)"

cd .agents/skills/engines-docstring-check && python -m scripts.docstrings check
cd .agents/skills/engines-agents-style-check && python -m scripts.check_engines_agents_style
```
