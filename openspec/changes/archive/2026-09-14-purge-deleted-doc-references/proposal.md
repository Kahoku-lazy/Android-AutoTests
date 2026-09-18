## Why

上一变更（`fix-dangling-skill-pointers`）把指向已删文档的活指针改到了现址，但按用户口径还需**彻底清除对这两份已删文档的痕迹**，并处理上一变更有意留白的三处：

| # | 位置 | 现状 | 要求 |
|---|------|------|------|
| 1 | `frontend/README.md` | 变更记录里仍以文件名提到 `DEVELOPMENT_CHECKLIST.md` 与 `VUE_API_CONTRACT.md` | 该文件整体删除（用户指示）——它已无入站引用（全仓检索 `frontend/README` = 0），内容由 `frontend/AGENTS.md` + 根 `README.md` 承接 |
| 2 | `plans/ai-assistant-vue-spec.md:3` | 「依据」列里仍有 `android-autotests-rules/references/frontend.md` | 清除该依据（用户指示：不保留 gitignored 例外） |
| 3 | `plans/ai-engine-abstraction.md:180` | P6 行要求「同步规则引用：`android-autotests-rules`（agent_scope 路径）」 | 改指现存规则文档，去掉已删技能 |
| 4 | `config/api_docs.py:521` | API 文档页脚文案里印着 `VUE_API_CONTRACT.md`（已删） | 清除该文案片段 |

## What Changes

- **删除** `frontend/README.md`（tracked；无入站引用；删除后可从 `git checkout frontend/README.md` 恢复）
- `plans/ai-assistant-vue-spec.md`：依据列表去掉已删技能，保留 `frontend/AGENTS.md` 与 `vue` skill
- `plans/ai-engine-abstraction.md` P6：规则引用改为 `apps/AGENTS.md` §1.2 通道收敛（真相源 `ARCH-00` §1.4 五条通信通道）
- `config/api_docs.py`：页脚去掉 `VUE_API_CONTRACT.md`（纯 HTML 文案片段，无行为影响）
- **BREAKING**：无
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 前置变更：`2026-09-14-fix-dangling-skill-pointers`（把活指针改到现址）
- 承接方：`frontend/AGENTS.md`（前端约束全文）· 根 `README.md`（文档索引）· `dev_docs/05-开发与测试/接口文档/API-*.md`（接口契约）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 文档：删 `frontend/README.md`；改 2 份 `plans/*.md`（gitignored）
- 源码：`config/api_docs.py` 的 1 行 HTML 文案（无逻辑改动）
- 验证：全仓检索 `VUE_API_CONTRACT` / `DEVELOPMENT_CHECKLIST` / `android-autotests-rules` 应为 0；`python -m py_compile config/api_docs.py` 通过；确认 `frontend/README.md` 无入站引用
