## 1. 复核（已完成）

- [x] 1.1 清点 `ai_assistant` 字面量：`api.py` 7 · `apps.py` 2 · `models.py` 4 · `provider_registry.py` 9 · `rag_service.py` 2 · `serializers.py` 8 · `model_test.py` 1 · `views_knowledge_drf.py` 3 · `views_drf.py` 8
- [x] 1.2 逐条判定，定出 **18 处**为真枚举值、其余为同形非枚举（dict/响应键 · Django 属性名 · 引擎原始状态）
- [x] 1.3 确认 `api.finalize_task(status=...)` 会 `task.status = status`，故 `views_drf.py:817` 与 `model_test.py:223` 的 `"completed"/"failed"` 确属 `TaskStatus`
- [x] 1.4 定下 `models.py` 不改（字段 default → 避迁移）
- [x] 1.5 **查实新缺陷**：`ModelProvider` 缺 `deepseek`/`gemini`（`PROVIDER_DEFAULTS` / `_PROVIDER_HOSTS` / `VALID_PROVIDERS` 都有），故 provider 字面量整块排除
- [x] 1.6 确认本 App 无契约转发模块，故按 D4 直连 `models.constants`

## 2. 修改

- [x] 2.1 `api.py`：+`from models.constants import AgentStatus, TaskStatus` + 5 行替换（`status="active"` ×2 同一替换）
- [x] 2.2 `apps.py`：+`TaskStatus` + 2 行替换
- [x] 2.3 `serializers.py`：+`MessageRole` + 5 行替换（含 role 白名单三元组）
- [x] 2.4 `views_drf.py`：+`AgentStatus, MessageRole, TaskStatus` + 5 行替换
- [x] 2.5 `management/commands/model_test.py`：+`TaskStatus` + 1 行替换
- [x] 2.6 新增 `tests/graybox/unit/test_ai_task_status_enums.py`（5 条）

## 3. 验证

- [x] 3.1 `python manage.py check` → 0 issues；`makemigrations --check --dry-run` → **`No changes detected`**（未碰 `models.py` 的设计生效）
- [x] 3.2 `python -m ruff check .` → **All checks passed!**；`ruff format --check .` → **248 files already formatted**
- [x] 3.3 新测试 **5 passed**；`pytest tests/graybox/unit tests/arch -q` → **109 passed**（104 + 新增 5）；`pytest tests/graybox/integration -q` → **16 passed**
- [x] 3.4 复扫字面量：剩余命中 **恰为 skip 名单**（`api.py:151/658` · `models.py` ×4 · `provider_registry.py` ×9 · `rag_service.py:233/297` · `serializers.py:53/61/173` · `views_drf.py:77/825/826` · `views_knowledge_drf.py:35/76/80`），零意外残留
- [x] 3.5 `--check-boundaries` → 零违规；范围：本单实际改动 `api.py` · `apps.py` · `serializers.py` · `views_drf.py` · `model_test.py`（`numstat` 中其余 ai_assistant 文件是**既有会话改动**，非本单）

## 4. 过程中的两个坑（值得记下）

1. **插入 import 会让后续「按行号替换」全部错位**：首版脚本先插 import 再按原行号替换，`AssertionError: LINE-MISS ... '    return list('`。而且插入方式对 `logger = ...` 这类锚点会**重复文本**（`model_test.py` 一度出现两行 `logger = ...` 与一个游离的 `)`）。
   **教训**：批量定点替换应先替换、后插 import；或干脆改用「唯一片段 + 出现次数断言」而非行号。
2. **最终采用的是片段法**：`text.count(old) == expected` 断言 + `replace`，18 处一次到位，且每个片段都断言了预期出现次数（`status="active"` 在 `api.py` 恰好 2 次，同一替换语义）。

## 5. 续做

1. **`ModelProvider` 补 `deepseek`/`gemini` 并让 provider 注册表以枚举为键**（收口 provider 字面量；涉及写入口校验与 base_url 白名单，独立裁决）
2. `models.py` 字段默认值仍是字面量（要收敛须先验证 Django 是否判字段变更）
3. `views_knowledge_drf` / `rag_service` 的 RAG 结果键（`"failed"` / `"indexed"`）不是域状态，已确认不属枚举域
