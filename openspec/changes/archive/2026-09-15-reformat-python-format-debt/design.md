## Context

`ruff format --check` 是 `apps/AGENTS.md` §3 关单清单的一部分。全仓 20 个既有文件不过，构成「改到就踩」的门禁陷阱。根因是行宽口径遗留（文件按更窄行宽折行，配置现为 100）。

范围口径修正：本单最初按 `apps/ config/ gateway/ shared/ models/` 量到 9 个文件；改用门禁原命令 `ruff format --check .` 后发现 `engines/` 与 `tests/` 另有 11 个 —— 教训是**量规必须与门禁命令同口径**，否则「修好一半」仍是红灯。

## Goals / Non-Goals

**Goals:**

- `python -m ruff format --check .` 归零，消除后续改动的门禁陷阱

**Non-Goals:**

- 不拆分超限文件（`ai_assistant/api.py` 848 · `element_locator/views.py` 1353）—— 体积项属独立 🔴 变更；拆分须与重排版分开，否则 review 无法分辨语义改动与纯格式改动
- 不改任何逻辑、标识符、注释文本或 `ruff.toml`

## Decisions

### 1. 一个专门的重排版变更，而不是塞进别的变更

- **选择**：独立 OpenSpec 变更，diff 全部是格式化构造
- **理由**：纯格式化 diff 会淹没真实语义改动。独立成单后，reviewer 可用「本单不应有任何语义改动」一句话验收；后续拆分 / 重构变更的 diff 也不再被格式噪音污染

### 2. 用工具而非手工重排

- **选择**：`python -m ruff format`
- **理由**：与门禁同源，保证「格式化结果」与「门禁判定」一致；手改不可能收敛

### 3. 用「去空白逐字节比对」证明无内容改动

- **选择**：对 20 个文件保留格式化前副本，比较 `"".join(text.split())`
- **理由**：`git diff --ignore-all-space` 无法识别**跨行重排**（它不合并行），会给出「几乎全改」的假象；去空白比对能把「真实内容变化」精确压到 5 处格式化构造（尾随逗号 ×3、括号化 ×2）

## Risks / Trade-offs

- [格式化意外改动语义] → ruff 格式化器不做语义改写；去空白比对已逐文件确认；再跑单测 / arch / 全仓 collect-only / `manage.py check` 兜底
- [括号化需要较新语法] → `target-version = "py313"`，实测 `python --version` 为 3.13.14；150 tests 可正常 collect
- [与后续拆分变更冲突] → 本单先落格式基线，后续拆分在同一基线上做，冲突面反而更小

## Migration Plan

1. `python -m ruff format` 20 个文件（先按 `ruff format --check .` 取准范围，不按 app 目录猜）
2. 去空白比对确认无内容改动；验证 `ruff format --check .`（0）· `ruff check .`（0）· `pytest tests/graybox/unit -q`（82）· `pytest tests/arch -q`（6）· `manage.py check`（0）
3. 归档；回滚 = 用 `temps/fmt_backup/` 下的 20 份格式化前副本还原（**不能**直接用 `git checkout`：`workflow/api.py` · `workflow/serializers.py` · `dashboard/ai_usage.py` · `element_locator/api_projects.py` 等含未提交的前序变更）
