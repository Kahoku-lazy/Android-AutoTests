## Why

`.agents/skills/android-autotests-rules/` 技能在本轮工作区被移除（`git status` 显示 6 个文件 `D`，目录已不在磁盘，且不在可用技能目录中）。但**全仓仍有 30+ 处引用它**（收尾清点：共 21 个文件、43 处指针，一并暴露了同样已删的 `工具-VUE_API_CONTRACT.md` 与 `DEVELOPMENT_CHECKLIST.md`），其中一部分还指向更早提交就已删除的 `frontend.md` / `backend.md` / `conventions.md` / `troubleshooting.md` / `database.md`（`git log --diff-filter=D` 显示这三份在 2026-09-01 的 `19b960aa` 与 2026-09-12 的 `a23dbdbb` 中被删）。

于是出现两层悬空指针：

1. **技能内部**：`vue-frontend-check` / `doodle-craft` / `django-backend-check` / `boundary-check` / `reviewer` 五个技能的「关联」段都指向已删文件；
2. **项目文档与代码**：`dev_docs`（入门指南 / 技术栈参考）· `frontend/README.md`（6 处）· `apps/自测与检测指令.md` · `apps/accounts/AGENTS.md` · `frontend/src/modules/workflow/index.vue` 的注释 · 以及 `apps/AGENTS.md` **自身**对 `architecture.md` / `backend.md` 的引用。

同批还有一份同源悬空：`dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md` 在本轮被删除（worktree `D`），而 `apps/AGENTS.md` 两处仍以它为契约对照真相源。

判据：以上引用逐个核对当前仓库里**同名/同主题的现存文档**后才改；没有继任者的按「主题归属」改到现在的权威文档，并在本变更表格里登记判断依据，绝不凭空造路径。

## What Changes

按下表把悬空指针改为现存权威文档（实际执行 21 个文件 · 43 处）（映射依据见括号）：

| 被删对象 | 现址（依据） |
|----------|--------------|
| `references/frontend.md` | `frontend/AGENTS.md`（前端约束唯一落点：L0–L3 速查 + Vue 规范 + 共享件） |
| `references/backend.md` | `apps/AGENTS.md`（后端约束唯一落点，标题即「Backend AGENTS.md」） |
| `references/api-conventions.md` | `.agents/skills/boundary-check/SKILL.md` §一（防火墙 #1–#4 已内联）+ `apps/AGENTS.md` §1.2/§1.3（L4 禁止 + 信封） |
| `references/architecture.md` §一 通道 | `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md` §1.4「五条通信通道」/§1.3「分层包图与防火墙」 |
| `references/architecture.md` §二/§七 | `ARCH-00` §3.1 模块依赖关系图 + `boundary-check` §二 引擎边界 |
| `references/python-code.md` | `apps/AGENTS.md` §1 + `ruff.toml`（配置真相源） |
| `references/security.md` | `apps/AGENTS.md` §1.2/§1.3（红线与契约）+ `config/env.py` / `config/settings.py`（凭据与安全配置）+ `frontend/AGENTS.md`（前端 XSS/清洗口径） |
| `references/conventions.md` | `frontend/AGENTS.md`「Vue 代码编写规范」+「前端项目结构」 |
| `references/troubleshooting.md` | `.agents/skills/vue-frontend-check/references/checklist.md`「常见断裂点（诊断线索）」 |
| `references/database.md` | `apps/AGENTS.md` §1.2（表前缀 / `db_table`）+ `ARCH-00` 附录 A.2 数据库表清单 |
| `dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md` | `dev_docs/05-开发与测试/接口文档/API-*.md`（11 份分端点契约） |
| `dev_docs/DEVELOPMENT_CHECKLIST.md`（dev_docs 重组时删除） | `.agents/skills/vue-frontend-check` · `django-backend-check` · `boundary-check`（现行关单门禁） |
| `.claude/rules/python-code.md`（`ruff.toml` 注释） | `apps/AGENTS.md` §1（团队 Python 规范） |

**范围**：只改指针文本（含 4 处代码注释 + 1 处测试 docstring + `ruff.toml` 注释），不动任何被指向文档的内容，不改任何行为。

**有意保留**：`plans/*.md`（gitignored 的历史计划文档，2 处）· `frontend/README.md` 变更记录里作为**历史**提到的 `DEVELOPMENT_CHECKLIST.md` / `VUE_API_CONTRACT.md`（它们记录的是当时做了什么，不是活指针）。

- **BREAKING**：无（全是文档/注释）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 改动落点：5 个技能 SKILL.md · `dev_docs/代码库入门指南.md` · `dev_docs/03-设计与架构/技术栈参考.md` · `frontend/README.md` · `apps/自测与检测指令.md` · `apps/accounts/AGENTS.md` · `apps/AGENTS.md` · `frontend/src/modules/workflow/index.vue`（注释）
- 迁移证据：`git log --diff-filter=D -- .agents/skills/android-autotests-rules` · `git ls-tree HEAD -- .agents/skills/android-autotests-rules` · 各现址文档的实际标题与章节名

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 文档/注释：**21 个文件 · 43 处指针**（5 个技能 SKILL/calibration · 5 份 dev_docs · 根 `README.md` · `frontend/README.md` · `apps/AGENTS.md` 与 `apps/accounts/AGENTS.md` · `apps/自测与检测指令.md` · 1 份 gitignored 报告）
- 源码：5 处注释/docstring（`frontend/src/modules/workflow/index.vue` · `frontend/src/style.css` · `gateway/routing.py` · `tools/gen_arch_stats.py` · `tests/arch/test_channels.py`）+ `ruff.toml` 注释，**无行为改动**
- 验证：全仓检索 11 个已删文件名 + `DEVELOPMENT_CHECKLIST` 只剩「变更记录里的历史提及」与 gitignored 的 `plans/`；`tests/arch/test_channels.py` **6 passed**；`ruff check` 通过（校验 `ruff.toml` 注释改动未破坏配置）
