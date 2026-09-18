## Why

🟡 **D4-1 的另一半：`ai_assistant` 的状态字面量未收敛到 `models/` 枚举**。前置两单已让设备域枚举真正生效（`activate-enum-ssot` · `migrate-ssot-enums-to-strenum` · `converge-device-literal-enums`）；`ai_assistant` 用的是另一批枚举，现状同构：

- `models/constants.py` 的 `AgentStatus` / `TaskStatus` / `MessageRole` 等 **零生产消费**；
- `AIAgent.status` / `AITask.status` / `AIMessage.role` 的字面量散在 `api.py` / `apps.py` / `serializers.py` / `views_drf.py` / `model_test.py` 五个文件里，共 **18 处**；
- 改一处状态口径要同时改多处，漏一处就是状态机静默分叉。

## What Changes

**收敛 18 处**（枚举成员替换字面量）：

| 文件 | 处数 | 枚举 |
|---|---:|---|
| `api.py` | 5 | `AgentStatus.ACTIVE` ×3 · `TaskStatus.PENDING` · `TaskStatus.RUNNING` |
| `apps.py` | 2 | `TaskStatus.RUNNING` · `TaskStatus.FAILED` |
| `serializers.py` | 5 | `MessageRole.ASSISTANT` ×3 · `MessageRole.USER``/`SYSTEM`（role 白名单） |
| `views_drf.py` | 5 | `MessageRole.USER``/`ASSISTANT` · `AgentStatus.ACTIVE` · `TaskStatus.COMPLETED``/`FAILED` ×2 |
| `management/commands/model_test.py` | 1 | `TaskStatus.COMPLETED``/`FAILED` |

- 五文件补 `from models.constants import ...`（`ai_assistant` 没有 `device_pool/contracts.py` 那样的契约转发模块，故直连 D4 规定的 SSOT 位置）
- 新增 `tests/graybox/unit/test_ai_task_status_enums.py`：钉住 `AITask` / `AIAgent` 的枚举写库读回普通取值串（与设备域同一手法）

- **BREAKING**：无。`StrEnum` 成员与字面量 `==` / 同 hash / `str()` 返回取值；`AITask.status` 是被前端轮询的状态字段，写库值不变
- 按 schema 约定设 `skip_specs: true`

## 明确**不改**的地方（逐条有理由）

| 位置 | 字面量 | 为什么不改 |
|---|---|---|
| `models.py` ×4 | `default="dashscope"` / `default="active"` ×2 / `default="pending"` | **避免迁移**：字段 `default` 参与 `deconstruct` |
| `api.py:148` · `serializers.py:52,60` · `rag_service.py:233` · `provider_registry.py` ×9 | `"dashscope"` / `"openai"` / `"anthropic"` / `"custom"` | **`ModelProvider` 枚举与真实提供商集合不一致**（见下）—— 此时收敛会写错 |
| `api.py:655` `obj.get("completed")` · `views_drf.py:822,823` · `views_knowledge_drf.py:35,76,80` · `rag_service.py:297` | `"completed"` / `"failed"` / `"running"` | 是**工具调用 / RAG 结果的字典键**，不是 `TaskStatus` |
| `views_drf.py:76` · `serializers.py:172` | `getattr(request, "user", None)` | 是 **Django request 属性名**，不是 `MessageRole` |
| `views_drf.py:819` | `"status": result.status` | 是**引擎原始状态**（`"success"` 等），不在 `TaskStatus` 取值域内 |

## 🟠 顺带查实的新缺陷（本单不修，登记待裁）

**`ModelProvider` 枚举不是提供商的 SSOT —— 它漏了实际在用的 2 个提供商**：

| 来源 | 提供商集合 |
|---|---|
| `provider_registry.PROVIDER_DEFAULTS`（有 base_url，供 `get_provider_config`） | `dashscope` `openai` `anthropic` **`deepseek`** **`gemini`** `custom` |
| `provider_registry._PROVIDER_HOSTS`（base_url 白名单校验） | 同上 5 个 |
| `provider_registry.VALID_PROVIDERS` = `frozenset(PROVIDER_DEFAULTS.keys())` → 被 `serializers` 用于写入口校验 | 同上 6 个 |
| `models.constants.ModelProvider` | `dashscope` `openai` `anthropic` `custom` —— **缺 `deepseek` / `gemini`** |

即「D4 声明的枚举 SSOT」比真实的提供商集合**少两个成员**；若按枚举收敛，`deepseek` / `gemini` 会被判为非法。修法（补枚举成员 + 让注册表以枚举为键）涉及产品口径与写入口校验，属独立裁决。

## 关联文档

- 契约真相源：`dev_docs/05-开发与测试/设计方案与报告/设计方案-Django设计系统分层.html` 行 269 / 331 / 375
- 前置变更：`activate-enum-ssot` · `migrate-ssot-enums-to-strenum` · `converge-device-literal-enums`（同手法，设备域）
- App 约束：`apps/ai_assistant/AGENTS.md` · `apps/AGENTS.md` §1.2
- 门禁：`django-backend-check/references/calibration.md` §2 · §7

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：`api.py` · `apps.py` · `serializers.py` · `views_drf.py` · `management/commands/model_test.py`（各 +1 import，共 18 行替换）
- 测试：新增 `tests/graybox/unit/test_ai_task_status_enums.py`
- 验证：`manage.py check` · `makemigrations --check`（**必须** `No changes detected`）· `ruff check .` / `ruff format --check .` · `pytest tests/graybox/unit tests/arch` · `--check-boundaries`
- 不在本单范围：`ModelProvider` 补 `deepseek`/`gemini` 并让注册表以枚举为键（独立裁决）· `models.py` 字段默认值
