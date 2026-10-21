## Context

动机见 `proposal.md`。当前实现约束（已实测）：

- 后端顶层包有 5 个：`config`、`apps`、`gateway`、`shared`、`models`；业务 App 9 个。
- 顶层 import 约 181 行、分布在 74 个 Python 文件；另有 `patch("apps...")`、`importlib.import_module("apps...migrations...")`、`shared.schema.target_class` 等字符串引用。
- `engines/` 只依赖 `utils.logs`，当前不 import `apps` / `config` / `shared` / `models`；`tests/` 依赖 `apps`、`shared`、`models`、`config`、`gateway`。
- 根 `manage.py` 设置 `DJANGO_SETTINGS_MODULE=config.settings`；`run.py` 在模块顶层 `from config.env import load_dotenv`；`run_daphne.py` 设置同一 settings 并以 `config.asgi:application` 启动。
- 测试配置已收敛到 `tests/pytest.ini` 与 `tests/test_settings.py`；根目录不再放 pytest 配置，执行入口为 `python -m pytest -c tests/pytest.ini`。
- `config/settings.py` 的 `BASE_DIR` 目前等于仓库根，`templates/`、`static/`、`logs/`、`data/`、`exports/`、`db.sqlite3` 都以它为基准。
- `config/env.py` 用 `Path(__file__).resolve().parent.parent` 定位仓库根并读取根 `.env`。
- `apps/report_generator/service.py` 用 `parent.parent.parent` 定位仓库根，写 `logs/` 与 `exports/`。
- CI 的 `backend-check` / `static-checks` / `security-scan` / `boundary-check` 都硬编码了 `apps/ config/ gateway/ shared/ models/` 或 `apps/` 扫描范围。
- 工作区存在并发会话的未提交改动；本变更实施时必须逐文件暂存，不能 `git add -A`。

## Goals / Non-Goals

**Goals:**

- 所有 Django 框架相关代码位于 `backend/`：`config/`、`apps/`、`gateway/`、`shared/`、`models/`、`templates/`、`static/`。
- 所有仓库内后端 import 使用 `backend.*` 命名空间，不再出现顶层 `apps.*` / `config.*` / `gateway.*` / `shared.*` / `models.*`。
- 保持 HTTP API、响应信封、数据库表名、Django app label、迁移历史、前端路由与页面行为不变。
- 保持 `engines/`、`tests/`、`utils/` 原位；它们仍以顶层包被引用。
- 根命令继续可用：`python manage.py check`、`python run.py start/check`、`python -m pytest -c tests/pytest.ini`。

**Non-Goals:**

- 不移动 `engines/`、`tests/`、`utils/`、`frontend/`、`openspec/`、`dev_docs/`。
- 不改任何 API 路径、字段名、信封形状、权限规则或业务逻辑。
- 不改 Django app label（`accounts`、`task_list` 等）与迁移文件名；因此不需要数据迁移。
- 不重命名 `models` 为 `domain`，不改 `engines` 内部结构。
- 不改写 `openspec/changes/archive/**` 的历史路径。
- 不把 `manage.py` / `run.py` / `run_daphne.py` 移入 `backend/`；它们是仓库入口，不是框架包。

## Decisions

### D1 `backend/` 是普通 Python 包，五个后端包整体下移

- 选择：新增 `backend/__init__.py`；`config/`、`apps/`、`gateway/`、`shared/`、`models/` 整体 `git mv` 到 `backend/` 下，形成 `backend.config`、`backend.apps`、`backend.gateway`、`backend.shared`、`backend.models`。
- 理由：import 路径与目录结构一致；`backend` 成为唯一后端根；避免「目录在 backend、import 还是顶层」的半迁移状态。
- 备选 A：只移动目录、保持顶层 import（需要把 `backend/` 加入 `sys.path`）。否决：与已确认的 `backend.models.constants` 目标冲突。
- 备选 B：把 `backend` 做成 src-layout（`backend/src/...`）。否决：多一层无收益，且会改变 `BASE_DIR` 与模板路径语义。

### D2 根入口保留，`backend.*` 依赖仓库根在 `sys.path`

- 选择：`manage.py`、`run.py`、`run_daphne.py` 留在仓库根；它们设置 `DJANGO_SETTINGS_MODULE=backend.config.settings`，`run.py` 的 ASGI 参数改为 `backend.config.asgi:application`。
- 理由：从仓库根执行 `python manage.py` 时，`sys.path[0]` 就是仓库根，`backend` 包可直接导入；不需要在每个入口里插 `sys.path`，也不需要改用户习惯。
- 备选：把入口移入 `backend/` 并在入口内 `sys.path.insert(0, parent)`。否决：入口会变成「先改路径再启动」的隐式魔法，且 `python backend/manage.py` 与 `python manage.py` 行为分叉。
- 约束：所有命令必须在仓库根执行；CI 与 `run.py` 已满足。

### D3 `engines` / `utils` / `tests` 保持顶层，后端以顶层名引用

- 选择：`backend.apps.*` 继续 `from engines...`、`from utils.logs...`；`tests/` 继续 `from backend...`。
- 理由：用户已明确 `engines` 与 `tests` 不移动；`utils.logs` 同时被 `engines` 与后端使用，移动会把 `engines` 一起拖入重构。
- 代价：`backend/` 不是完全自包含，运行时仍要求仓库根在 `sys.path`。这与 D2 一致，且当前所有启动方式都从仓库根出发。
- 备选：把 `utils` 移入 `backend.utils`。否决：`engines` 会被迫改 import，违背「engines 不移动」的范围。

### D4 只改 `AppConfig.name`，保留 `label` 与迁移历史

- 选择：9 个 `apps.py` 的 `name = "apps.X"` 改为 `name = "backend.apps.X"`；已有显式 `label`（如 `accounts`）保持不变，未显式声明的 App 继续使用最后一段作为 label。
- 理由：Django 的迁移依赖与 `django_migrations.app` 记录使用 **label**，不是完整模块路径；保留 label 可避免任何数据迁移或迁移历史断裂。
- 验证：`python manage.py makemigrations --check` 必须无新迁移；`python manage.py showmigrations` 的 app 列表与迁移前一致。
- 备选：把 label 也改成 `backend_apps_X`。否决：会制造迁移历史断裂，收益为零。

### D5 `BASE_DIR` 改为 `backend/`，运行数据仍留在仓库根

- 选择：在 `backend/config/settings.py` 中显式定义：
  - `BASE_DIR = Path(__file__).resolve().parent.parent`（即 `backend/`）
  - `REPO_ROOT = BASE_DIR.parent`（即仓库根）
  - `TEMPLATES["DIRS"] = [BASE_DIR / "templates"]`
  - `STATICFILES_DIRS = [BASE_DIR / "static"]`
  - `STATIC_ROOT = REPO_ROOT / "staticfiles"`
  - `DATA_DIR` 默认 `REPO_ROOT / "data"`
  - `LOG_DIR = REPO_ROOT / "logs"`
  - `EXPORT_DIR = REPO_ROOT / "exports"`
  - SQLite `NAME = REPO_ROOT / "db.sqlite3"`
- 理由：代码位置变了，但日志、上传、导出、SQLite 文件的位置不应变；否则现有开发库、日志采集与运维脚本会全部找不到文件。
- `backend/config/env.py` 的 `ROOT` 改为 `Path(__file__).resolve().parents[2]`（`backend/config/env.py` → `backend/config` → `backend` → 仓库根），继续加载根 `.env`。
- `backend/apps/report_generator/service.py` 的 `BASE_DIR` 改为 `Path(__file__).resolve().parents[3]`，或在模块内改用 `settings.REPO_ROOT`；优先后者，避免再次出现层级假设。
- 备选：让 `BASE_DIR` 继续等于仓库根（通过 `parents[3]`）。否决：`templates/`、`static/` 已移入 `backend/`，继续用仓库根会让模板查找失效。

### D6 import 迁移只做前缀替换，不改相对 import

- 选择：对 `backend/` 内文件，`from apps...` → `from backend.apps...`，`from config...` → `from backend.config...`，`from gateway...` → `from backend.gateway...`，`from shared...` → `from backend.shared...`，`from models...` → `from backend.models...`；`from .` / `from ..` 全部不动。
- 选择：`tests/` 与 `utils/` 中的顶层 import 同样加 `backend.` 前缀；`engines/` 不动。
- 选择：字符串引用单独处理，不依赖 import 重写：
  - `shared/schema.py` 的 `target_class`
  - `settings.py` 的 `INSTALLED_APPS` / `MIDDLEWARE` / `DEFAULT_AUTHENTICATION_CLASSES` / `DEFAULT_RENDERER_CLASSES`
  - `config/urls.py` 的 `include("apps...")`
  - 测试中的 `patch("apps...")`、`importlib.import_module("apps...")`
  - 测试中的 `shared.renderers...` 断言
- 理由：字符串引用不会被 ruff/isort 发现，必须单独 grep 验证；相对 import 不涉及包名，不应制造无意义 diff。

### D7 工具链按「仓库根 + backend/ 前缀」调整

- `tests/pytest.ini`：`DJANGO_SETTINGS_MODULE = tests.test_settings`；`testpaths = .` 不变；执行入口保持 `python -m pytest -c tests/pytest.ini`。
- `tests/test_settings.py`：`from backend.config.settings import *`。
- `ruff.toml`：`known-first-party = ["backend", "engines", "utils"]`；`per-file-ignores` 中 `config/settings.py` 改为 `backend/config/settings.py`，`tests/test_settings.py` 保持不变。
- `pyproject.toml`：`coverage.run.source = ["backend/apps"]`。
- `utils/check_gates.py`：`PY_SCOPES` 改为 `backend/apps/`、`backend/config/`、`backend/gateway/`、`backend/shared/`、`backend/models/`；`_env()` 的 settings 改为 `backend.config.settings`；pytest 命令使用 `-c tests/pytest.ini`。
- `utils/gen_arch_stats.py`：`PROJECT_ROOT / "apps"` 改为 `PROJECT_ROOT / "backend" / "apps"`；app 识别仍按 `apps/` 子串，避免重写统计逻辑。
- `utils/check_openapi_coverage.py`：settings 改为 `backend.config.settings`；`sys.path` 仍插仓库根。
- `dsh-plugins/arch-gate/src/index.ts`：`pathGlobs` 改为 `backend/apps/**/*.py`；脚本路径 `utils/gen_arch_stats.py` 不变。
- `.github/workflows/ci-phase1.yml`：ruff 路径、安全扫描 grep 路径、`pytest -c tests/pytest.ini`、OpenAPI 相关路径改为 `backend/`；`python manage.py check` 与 pytest 仍从仓库根执行。
- 理由：工具链是这次重构最容易「看起来绿、实际扫空」的部分；所有扫描范围必须指向新目录。

### D8 迁移顺序：先移动，再改 import，再改路径，最后跑门禁

1. 记录当前 `git status`，把并发会话改动与本变更隔离；只暂存本变更文件。
2. `git mv` 七个目录与 `backend/__init__.py`；此提交不做内容修改，保证 Git 识别为 rename。
3. 全局替换 import 前缀（仅限 `backend/`、`tests/`、`utils/`），跑 `ruff check --fix` 只处理 import 顺序，不跑全仓格式化。
4. 更新 Django 配置、AppConfig、入口、`BASE_DIR` / `.env` / 日志路径。
5. 更新 pytest/ruff/coverage/CI/架构门禁/测试字符串引用。
6. 运行 `python manage.py check`、`makemigrations --check`、`python -m pytest -c tests/pytest.ini --collect-only`、`python run.py check`。
7. 更新文档与 AGENTS 路径，最后归档变更。
- 回滚：本变更不含数据库迁移；`git revert` 对应提交即可恢复目录与 import。若只回滚部分提交，必须保证 `backend/` 目录与 import 前缀同时回滚，不能只回滚一半。

## 模块防火墙自检

- 跨 App import：本变更不新增任何跨 App 依赖，只把既有 `apps.*` 改为 `backend.apps.*`；原有限制（只读 Model、写走 `api.py`）不变。
- 禁止跨 App import service/runner/consumer/state_machine：既有 import 关系原样保留，不借重构放宽边界。
- 写库归口：所有 `INSERT/UPDATE/DELETE` 仍在各 App `api.py`；本变更只改模块路径，不改调用链。
- 前端不直连数据库：本变更不碰 `frontend/`。
- 新跨模块依赖：无。`backend.apps.*` 仍只通过既有 `api.py` / Model 只读关系互相引用。

## Risks / Trade-offs

- [根入口从 `backend/` 内部启动时找不到 `backend` 包] → 明确约定所有命令从仓库根执行；`run.py`、CI、`pytest` 均从根启动；入口不提供 `backend/manage.py`。
- [`BASE_DIR` 变化导致模板/静态/日志/上传路径漂移] → 用 `BASE_DIR` + `REPO_ROOT` 双变量，逐项确认 `templates`、`static`、`logs`、`data`、`exports`、SQLite 的目标位置；启动后实测 `/api/swagger/` 与上传。
- [AppConfig.name 改了但 label 漂移] → 显式保留 `label`；`makemigrations --check` 与 `showmigrations` 双重验证。
- [字符串引用漏改（patch/import_module/schema target）] → 全文 grep `"apps.`、`"config.`、`"shared.`、`"gateway.`、`"models.`；单测收集必须全绿。
- [CI 扫描范围漏改，门禁扫空] → 逐项改 `PY_SCOPES`、ruff 路径、安全扫描、arch-gate glob；用 `--collect-only` 与 `run.py check` 验证实际扫描到文件。
- [并发会话改动混入] → 实施前记录 `git status --short`，只 `git add` 本变更文件，禁止 `git add -A`。
- [迁移期间前后端同时启动，旧进程仍加载旧模块] → 改完后重启后端；`run.py restart backend`，不依赖热重载。
- [文档路径滞后，后续变更继续写旧路径] → 同步 `AGENTS.md`、`README.md`、`backend/apps/AGENTS.md`、`openspec/schemas/android-autotests/templates/tasks.md`；历史归档不改。

## Migration Plan

1. **预检**：确认工作区状态；记录并发改动清单；确认 `backend/` 不存在。
2. **目录移动**：`git mv config backend/config`、`git mv apps backend/apps`、`git mv gateway backend/gateway`、`git mv shared backend/shared`、`git mv models backend/models`、`git mv templates backend/templates`、`git mv static backend/static`；新增 `backend/__init__.py`。
3. **import 重写**：`backend/`、`tests/`、`utils/` 内的五个顶层前缀统一加 `backend.`；`engines/` 不动；相对 import 不动。
4. **Django 配置**：`settings.py`、`test_settings.py`、`asgi.py`、`urls.py`、`manage.py`、`run.py`、`run_daphne.py`、9 个 `apps.py`、`shared/schema.py`。
5. **路径语义**：`BASE_DIR` / `REPO_ROOT` / `.env` / `logs` / `data` / `exports` / SQLite / `templates` / `static`；`report_generator/service.py`。
6. **工具链**：pytest、ruff、coverage、check_gates、gen_arch_stats、check_openapi_coverage、arch-gate、CI。
7. **测试字符串**：`patch(...)`、`importlib.import_module(...)`、`shared.renderers` / `shared.auth` 断言。
8. **验证**：`python manage.py check`、`python manage.py makemigrations --check`、`python -m pytest -c tests/pytest.ini --collect-only -q`、`python run.py check`、启动后端实测 `/api/swagger/` 与 `/api/tasks/`。
9. **文档**：`AGENTS.md`、`README.md`、`backend/apps/AGENTS.md`、`apps/自测与检测指令.md`、OpenSpec 模板中的路径。
10. **回滚**：`git revert` 迁移提交组；不涉及数据库迁移，回滚后重启后端即可。

## Open Questions

（无）
