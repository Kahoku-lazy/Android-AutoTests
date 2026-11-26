## Why

Engines 的「模块头 4 字段」注释方案（模块功能 / Python 调试 / 时间 / 测试）只在 `engines/**` 生效（`.agents/rules/engines-code-style.md` §1），
其余 Python 代码仍停留在自由格式 docstring：同一个仓库两套注释语言，人读代码要先分辨「这是 engines 还是别的」，
机器检查（`engines-docstring-check`）也只覆盖 12% 的 Python 文件。

## What Changes

- **规范层**：新增全仓规则 `.agents/rules/python-docstring-style.md`，作为 4 字段模板的**唯一真相源**；
  `.agents/rules/engines-code-style.md` §1/§2 改为指向它，engines 只保留「工具函数（`FunctionTool`）摘要 + `Args:`」这条专规；
  根 `AGENTS.md`「文档与工具说明」加一行指路。
- **范围层（本次裁定的排除清单）**：以下 Python 代码**不写** 4 字段模块头：
  - Django 固定脚手架（**仅 `backend/**` 下**）：`models.py`、`views.py`、`views_*.py`、`*_views.py`、`api.py`、`api_*.py`、`serializers*.py`、`admin.py`、`urls.py`、`apps.py`、`asgi.py`、`wsgi.py`、`settings.py`、根 `manage.py`，以及 `backend/**/migrations/**`；
  - 非产品代码：`.agents/**`、`temps/**`、`dev_docs/**`、`openspec/**`、`frontend/**`、`.venv`/`.dvenv`/`node_modules` 等依赖与缓存目录。
  - 例外：`engines/**/models.py` 是引擎领域模型，**照常检查**（按文件名排除只在 `backend/` 下生效）。
- **机制层**：`engines-docstring-check` 的 `check` 从「只看 engines」改为「全仓在册范围 + 排除清单」，
  `--all` 扫描全仓在册文件，改动模式默认只报本次新引入；新增 `--summary` 输出按规则聚合的计数；
  `python -m run check` 增加**非阻塞**门禁 `python-module-docstring`（先看效果，暂不拦 CI）。
- **代码层（存量迁移，分批）**：开工时在册 465 个文件、达标的只有 91 个（89 个在 engines）。
  批次 1（`utils/**` 26 + 根脚本 2 + engines 残留 2）、批次 2（`tests/**` 118）、批次 3（`backend/**` 非固定结构 58）已全部归零；
  并行提交把单元测试层整体迁到 `temps/`（不纳入本规范），因此现在在册 **328** 个、**0 error**。
  **只重排注释，不改语义**。
- **BREAKING**：无运行时行为变更；对开发者而言，新增 Python 文件不再能只写自由格式 docstring。

## 关联文档

无 PRD 编号：属**代码风格规范 + 工具链**类变更，不改变平台行为（与 `fix-module-doc-drift` 同类）。
需求方裁定记录在 `design.md` D1–D5（2026-11-24 会话，5 个边界问题逐条确认）。

## Capabilities

### New Capabilities

（无 —— 纯规范与工具链，无行为变更；`.openspec.yaml` 已设 `skip_specs: true`）

### Modified Capabilities

（无）

## Impact

- **规范文档**：新增 `.agents/rules/python-docstring-style.md`；修改 `.agents/rules/engines-code-style.md`（§1/§2/§8）、根 `AGENTS.md`（加一行指路）、`.agents/skills/engines-docstring-check/SKILL.md`。
- **工具**：`.agents/skills/engines-docstring-check/scripts/docstrings.py`（范围与输出）、`utils/check_gates.py`（新增非阻塞门禁）。
- **代码（分批迁移）**：`utils/**` 26 个、根 `run.py` / `run_daphne.py`、`tests/**` 约 255 个、`backend/**` 非固定结构 91 个、`engines/**` 2 个残留。
- **不动的**：Django 固定脚手架 232 个、`.agents/**`/`temps/**`/`dev_docs/**` 等 47 个。
- **回退**：单文件回退 = `git checkout` 该文件；整批回退 = 还原对应提交；规则层回退 = 还原三份 md 与检查器提交，删除新增门禁条目。

### 变更申请（改什么 / 为什么必须 / 影响面 / 怎么回退）

| 项 | 内容 |
| --- | --- |
| 改什么 | ① 新增全仓注释规范并让 `engines-code-style.md` §2 指向它；② 根 `AGENTS.md` 加一行指路；③ 检查器作用域从 engines 扩到全仓在册范围；④ `run.py check` 增非阻塞门禁 |
| 为什么必须 | 用户 2026-11-24 明确要求「把 Engines 的注释方案推广到除 Django 固定结构外的所有 Python 代码」；不落规范正文与检查器，新规则无人执行、两套口径继续并存 |
| 影响面 | 不改任何 AGENTS.md 红线 / 禁止事项 / 准入清单 / 依赖边界条款；不改任何运行时行为；触发点在「新写的 Python 文件」与「被改动到的存量文件」 |
| 怎么回退 | 还原 `.agents/rules/engines-code-style.md`、根 `AGENTS.md`、删 `.agents/rules/python-docstring-style.md`、还原检查器与门禁条目；存量迁移按目录整批 revert |
