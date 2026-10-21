## Why

当前仓库根目录同时承担「后端项目根」和「monorepo 根」两种角色：`frontend/` 是显式子项目，而 Django 的 `config/`、`apps/`、`gateway/`、`shared/`、`models/`、`templates/`、`static/` 全部散落在仓库根。新人无法一眼判断哪些目录属于后端，路径规则也靠口头约定维护。本变更把 Django 后端代码收进 `backend/`，并统一使用 `backend.*` 导入命名空间，让前后端边界在目录和 import 两个层面都显式可见。

## What Changes

- **BREAKING**（仅对仓库内 Python 调用方）后端顶层包改名：
  - `config.*` → `backend.config.*`
  - `apps.*` → `backend.apps.*`
  - `gateway.*` → `backend.gateway.*`
  - `shared.*` → `backend.shared.*`
  - `models.*` → `backend.models.*`
- 目录移动：
  - `config/` → `backend/config/`
  - `apps/` → `backend/apps/`
  - `gateway/` → `backend/gateway/`
  - `shared/` → `backend/shared/`
  - `models/` → `backend/models/`
  - `templates/` → `backend/templates/`
  - `static/` → `backend/static/`
  - 新增 `backend/__init__.py`
- Django 配置同步：`INSTALLED_APPS`、各 `AppConfig.name`、`MIDDLEWARE`、`ROOT_URLCONF`、`ASGI_APPLICATION`、DRF 认证/渲染器、Jazzmin 图标键全部改为 `backend.*`；`label` 保持不变，避免影响迁移历史与 `django_migrations`。
- 入口同步：根 `manage.py`、`run.py`、`run_daphne.py` 保持为入口，但 `DJANGO_SETTINGS_MODULE`、ASGI 路径、`sys.path` 改为指向 `backend.*`。
- 路径语义同步：`BASE_DIR` 变为 `backend/`；`.env`、`logs/`、`data/`、`exports/`、SQLite 数据库仍保留在仓库根，通过显式 `REPO_ROOT` 保持现状。
- 工具链同步：pytest、ruff、coverage、`utils/check_gates.py`、`utils/gen_arch_stats.py`、`dsh-plugins/arch-gate`、CI 6 个 job 的路径与 `PY_SCOPES` 全部改为 `backend/`。
- 测试同步：根 `tests/` 保留，所有 `apps.*` / `config.*` / `shared.*` / `models.*` 的 import、patch 字符串、migration import 字符串统一改为 `backend.*`；`engines/` 与 `tests/` 目录本身不移动。
- 文档同步：`AGENTS.md`、`README.md`、`apps/AGENTS.md` 等路径引用改为 `backend/`；历史归档不改写。

## 关联文档

无。本变更为纯目录与导入命名空间重构，不改变任何 HTTP API、页面行为或业务规则；`openspec/specs/` 下没有能力描述「Python 包位于仓库根」，故在 `.openspec.yaml` 声明 `skip_specs: true`。

## Capabilities

### New Capabilities

（无：本次不引入新的业务能力，验收由 `python run.py check` 与 CI 6 个 job 承担。）

### Modified Capabilities

（无：所有能力的行为契约不变，仅实现位置与 import 路径变化。）

## Impact

- **代码（后端）**：`config/`、`apps/`、`gateway/`、`shared/`、`models/` 共 5 个顶层包；9 个业务 App 的 `apps.py`；`templates/`、`static/`。
- **入口**：根 `manage.py`、`run.py`、`run_daphne.py`。
- **导入面**：静态检索到约 181 行顶层 import、74 个文件；另有 migration 测试的 `importlib.import_module("apps...")`、`patch("apps...")`、`shared.schema.target_class` 等字符串引用。
- **工具链**：`pytest.ini`、`ruff.toml`、`pyproject.toml`、`utils/check_gates.py`、`utils/gen_arch_stats.py`、`utils/check_openapi_coverage.py`、`dsh-plugins/arch-gate`、`.github/workflows/ci-phase1.yml`。
- **测试**：`tests/` 保留原位，但 import 与路径断言需要更新；`tests/engines/` 不动。
- **不移动**：`engines/`、`tests/`、`utils/`、`frontend/`、`openspec/`、`dev_docs/`；`engines` 继续以顶层 `engines.*` 被后端引用，`utils` 继续以 `utils.*` 被后端与引擎引用。
- **不影响**：HTTP API 路径、响应信封、前端页面与路由；数据库表名与迁移历史；`engines` 内部 import；历史归档文档。
