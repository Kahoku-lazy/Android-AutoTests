## Why

🟡 **仓库 `ruff format` 门禁未过**（D2-7 的格式侧）：`python -m ruff format --check .` 报 **20 个文件需要重排版**，全部是**既有债**（无一由本会话引入）：

| # | 文件 | 重排 churn (+/-) |
|---|------|---:|
| 1 | `apps/ai_assistant/api.py` | 1 / 3 |
| 2 | `apps/ai_assistant/rag_service.py` | 10 / 2 |
| 3 | `apps/dashboard/ai_usage.py` | 1 / 4 |
| 4 | `apps/element_locator/admin.py` | 9 / 1 |
| 5 | `apps/element_locator/api_directories.py` | 6 / 2 |
| 6 | `apps/element_locator/api_projects.py` | 7 / 7 |
| 7 | `apps/element_locator/views.py` | 4 / 1 |
| 8 | `apps/workflow/api.py` | 15 / 12 |
| 9 | `apps/workflow/serializers.py` | 3 / 3 |
| 10-11 | `engines/__init__.py` · `engines/ai/__init__.py` | 1/1 each |
| 12-14 | `engines/ai/agentscope/{model,tool_wrapper,workflow}.py` | 6/7 · 4/4 · 1/3 |
| 15 | `tests/e2e/conftest.py` | 6 / 2 |
| 16-17 | `tests/graybox/integration/test_device_{serializer,state_machine}.py` | 2/6 each |
| 18 | `tests/graybox/unit/test_case_manager_projects.py` | 2 / 6 |
| 19 | `tests/graybox/unit/test_device_detector.py` | 48 / 28 |
| 20 | `tests/graybox/unit/test_example_unit.py` | 6 / 1 |
| | **合计** | **135 / 100**（235 行） |

根因是**行宽口径变更遗留**：这些文件按更窄行宽折行，而 `ruff.toml` 现为 `line-length = 100`，格式化器于是要把它们**合并**回单行。

危害是**门禁陷阱**：`apps/AGENTS.md` §3 关单清单要求 `ruff format --check（相关路径）`，因此任何后续改动只要碰到这 20 个文件之一，就必须在「夹带无关重排」与「门禁红灯」之间二选一 —— 上一个变更 `fix-workflow-directory-update-atomicity` 正撞上这一点（见其归档 `tasks.md`「遗留」段，其中记的「9 个」是 apps 范围的旧口径，本次实测全仓为 20 个）。

## What Changes

- 对上述 20 个文件运行 `python -m ruff format`
- 已逐文件用「备份 vs 格式化后，去掉全部空白再比对」验证：**5 个文件有内容差异，全部是格式化构造**（尾随逗号 3 处、折行所需括号化 2 处）；其余 15 个文件去掉空白后**逐字节相同**
  - 尾随逗号：`rag_service.py`（dict）· `element_locator/admin.py`（tuple）· `test_example_unit.py`（list）
  - 括号化：`apps/workflow/api.py`（多条件 `if` 加括号折行）· `test_device_detector.py`（多上下文管理器 `with (...)`）
  - 无任何标识符、字符串、数值、注释文本或控制流被改动
- 不改 `ruff.toml`（配置本身已正确）

- **BREAKING**：无 —— 只改空白、折行、尾随逗号与折行所需括号；由 `tests/graybox/unit`（82 passed）· `tests/arch`（6 passed）· 全仓 `--collect-only`（150 tests collected）· `manage.py check` 兜底
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 门禁真相源：`apps/AGENTS.md` §3 关单清单 · `.agents/skills/django-backend-check/references/calibration.md` §2 🟡「`ruff format` 未过」· §7 强制命令
- 前置变更：`restore-repo-lint-gate`（2026-09-15 归档，修 `ruff check .` 侧）—— 本单是其**格式侧收尾**
- 前置变更：`fix-workflow-directory-update-atomicity`（2026-09-15 归档）的「遗留」段记录了本单要清的 workflow 两文件

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：20 个既有 Python 文件（`apps/` ×9 · `engines/` ×5 · `tests/` ×6），仅格式化
- 验证：`python -m ruff format --check .` → **243 files already formatted**（0 待重排）· `python -m ruff check .` → All checks passed · `pytest tests/graybox/unit -q` → 82 passed · `pytest tests/arch -q` → 6 passed · `python manage.py check` → 0 issues
- 不在本单范围：`apps/ai_assistant/api.py`（848 行 → 超 api 上限 2×，🔴）、`apps/element_locator/views.py`（1353 行 → 4.5×，🔴）等**体积超限**项（calibration §4「只允许拆分」）。本单只重排版、不拆分：拆分须与纯格式改动分开，否则 review 无法分辨语义与格式
