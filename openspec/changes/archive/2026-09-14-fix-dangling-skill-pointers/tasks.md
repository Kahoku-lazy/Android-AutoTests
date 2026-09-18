## 1. 事实与映射

- [x] 1.1 确认被删技能状态；验证：`Test-Path .agents/skills/android-autotests-rules` = false；`git status` 显示 6 个 `D`；`git ls-tree HEAD` 仅列 SKILL.md + api-conventions/architecture/python-code/security/setup.md；该技能不在可用技能目录中
- [x] 1.2 确认更早删除的文件与提交；验证：`git log --diff-filter=D` 显示 `a23dbdbb`(2026-09-12) 删 `frontend.md`、`19b960aa`(2026-09-01) 删 `backend.md` / `conventions.md` / `database.md` / `troubleshooting.md` / `agentscope-tools.md`
- [x] 1.3 确立现址映射；验证：11 条映射每条目标都 `Test-Path` 为真或章节名可在现文档中检索到（`ARCH-00` §1.4「五条通信通道」· §1.3「分层包图与防火墙」· `boundary-check` §一「模块边界（防火墙）」/§二「引擎边界」· `apps/AGENTS.md` §1.2/§1.3 · `gateway/middleware.py::_is_public` · `vue-frontend-check/references/checklist.md`「常见断裂点」）

## 2. 技能内指针（6 个文件）

- [x] 2.1 `vue-frontend-check/SKILL.md`：`references/frontend.md` → `frontend/AGENTS.md`；同时把同段的失效 `AGENTS.md §2` 指针改为「硬性规范 §1.14 + `tokens.css` 刻度注释」（上一变更已改，此处复核）
- [x] 2.2 `doodle-craft/SKILL.md`：`references/frontend.md` → `frontend/AGENTS.md`
- [x] 2.3 `django-backend-check/SKILL.md`：四个引用 → `apps/AGENTS.md` + `ruff.toml` + `boundary-check`
- [x] 2.4 `django-backend-check/references/calibration.md`：`与 python-code.md 对齐` → `与 apps/AGENTS.md 的文件上限、ruff.toml 对齐`
- [x] 2.5 `boundary-check/SKILL.md` 三处：`architecture.md §一` → `ARCH-00 §1.4 五条通信通道`；索引表两行 → `ARCH-00`（§1.4/§1.3/§3.1）与「本 skill §一（防火墙 #1–#4 已内联）」
- [x] 2.6 `reviewer/SKILL.md` 三处：`security.md` → `apps/AGENTS.md` §1.2/§1.3 + `config/env.py` / `settings.py` + `frontend/AGENTS.md`；`references/frontend.md` → `frontend/AGENTS.md`；`references/backend.md` + `references/api-conventions.md` → `apps/AGENTS.md` + `ruff.toml` + `boundary-check`

## 3. 项目文档（9 个文件）

- [x] 3.1 `dev_docs/代码库入门指南.md`：skill 引用 → 前端读 `frontend/AGENTS.md`、后端读 `apps/AGENTS.md`；`工具-VUE_API_CONTRACT.md` → `接口文档/API-*.md`
- [x] 3.2 `dev_docs/03-设计与架构/技术栈参考.md` 两处 → `frontend/AGENTS.md`（L0–L3 速查 + Vue 规范）
- [x] 3.3 `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md` 文件地图：删掉已不存在的 `工具-VUE_API_CONTRACT.md`
- [x] 3.4 `frontend/README.md`：时效指针 8 处（3 处 `frontend.md`/`conventions.md`/`troubleshooting.md` · 3 处 `工具-VUE_API_CONTRACT.md` · 2 处 `DEVELOPMENT_CHECKLIST.md`）→ `frontend/AGENTS.md` / `boundary-check` / `vue-frontend-check` 清单 / `接口文档/API-*.md` / 关单门禁技能；顺带把 `§2（风格规则）` 改指 §1 硬性规范，并把一行错误的信封 `{ok, data/error}` 改为 `{status, data}`
- [x] 3.5 `apps/自测与检测指令.md` 三处：`python-code.md` → `apps/AGENTS.md` §1 · 章节标题同改 · `api-conventions.md` → `boundary-check` §一 + `apps/AGENTS.md` §1.2
- [x] 3.6 `apps/accounts/AGENTS.md` 三处：`backend.md` → `gateway/middleware.py::_is_public` · `config/env.py` / `settings.py`（×2 行）
- [x] 3.7 根 `README.md`：`DEVELOPMENT_CHECKLIST.md` → 三个关单门禁技能
- [x] 3.8 `dev_docs/05-开发与测试/设计方案与报告/设计方案-AgentScope设计系统分层.html`：把「通道 SSOT 悬空」风险项改为已收敛（附本变更名）
- [x] 3.9 有意保留：`plans/*.md`（gitignored 历史计划，2 处）· `frontend/README.md` 变更记录里的历史提及；验证：见 5.2 的命中说明

## 4. `apps/AGENTS.md` 自引用与代码注释（5 个文件）

- [x] 4.1 `apps/AGENTS.md` 6 处：`architecture.md §一` ×2 → `ARCH-00` §1.4；`backend.md` ×2 → `gateway/middleware.py::_is_public` 与 `config/env.py`/`settings.py`；`工具-VUE_API_CONTRACT.md` ×2 → `接口文档/API-*.md`
- [x] 4.2 `frontend/src/modules/workflow/index.vue`：z-index 注释出处 → `frontend/AGENTS.md`「L5 覆盖层」
- [x] 4.3 `frontend/src/style.css`：滚动策略注释出处 → `frontend/AGENTS.md`「L3 容器」/「L0 层速查」
- [x] 4.4 `gateway/routing.py`：模块 docstring 的 `architecture.md` → `ARCH-00` §1.4
- [x] 4.5 `tools/gen_arch_stats.py`：引擎泄漏规则出处 `architecture.md §七` → `boundary-check/SKILL.md §二 引擎边界`；`tests/arch/test_channels.py` docstring 同改 → `ARCH-00` §1.4；`ruff.toml` 注释 → `apps/AGENTS.md` §1

## 5. 验证

- [x] 5.1 新目标存在性；验证：映射表中的每个路径 `Test-Path` 为真（`frontend/AGENTS.md` · `apps/AGENTS.md` · `boundary-check/SKILL.md` · `ARCH-00-平台总体架构.md` · `接口文档/` · `vue-frontend-check/references/checklist.md` · `config/env.py` · `gateway/middleware.py` · `ruff.toml`），章节名逐一检索确认
- [x] 5.2 旧路径清零；验证：全仓检索 11 个已删文件名 + `DEVELOPMENT_CHECKLIST`（尊重 .gitignore）→ 仅剩 `frontend/README.md:115` 的**变更记录历史提及**；显式检索 gitignored 文件 → `plans/*.md` 2 处（有意保留）+ 本变更文档自身；被改报告项已改为「已收敛」
- [x] 5.3 范围与回归；验证：`tests/arch/test_channels.py` **6 passed**；`ruff check` 通过；`git diff --numstat` 覆盖 21 个文件且仅注释/文档行变化，无逻辑改动
