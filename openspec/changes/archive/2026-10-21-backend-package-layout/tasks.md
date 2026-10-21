## 1. 预检与隔离

- [x] 1.1 如后端/前端正在运行，先执行 `python run.py stop backend frontend`；验证：`python run.py status` 显示 backend/frontend 未监听，避免 Windows 文件占用导致 `git mv` 失败。
- [x] 1.2 记录迁移前工作区：`git status --short` 与 `git diff --cached --name-only` 写入 `temps/backend-layout-baseline.txt`；验证：文件存在，且能据此区分并发会话改动与本变更文件。
- [x] 1.3 确认 `backend/` 尚不存在且当前分支为 `Kahoku`；验证：`Test-Path backend` 为 `False`，`git branch --show-current` 输出 `Kahoku`。

## 2. 目录移动

- [x] 2.1 用 `git mv` 移动 `config/`、`apps/`、`gateway/`、`shared/`、`models/`、`templates/`、`static/` 到 `backend/` 下；验证：`git status --short` 显示 7 项 `R`（重命名），`backend/` 下 7 个目录齐全，仓库根不再有这 7 个目录。
- [x] 2.2 新增 `backend/__init__.py`，内容仅包说明、不得 import 任何模块；验证：`python -c "import backend"` 退出码 0 且无输出。
- [x] 2.3 检查移动后空目录与遗漏文件；验证：`Get-ChildItem backend -Recurse -File` 中包含 `manage.py` 之外的预期文件，根目录无残留 `apps/`、`config/`、`gateway/`、`shared/`、`models/`、`templates/`、`static/`。

## 3. 导入命名空间迁移

- [x] 3.1 将 `backend/` 内所有 `from apps|config|gateway|shared|models` / `import ...` 改为 `backend.` 前缀；相对 import（`from .` / `from ..`）不动；验证：`Select-String -Path backend -Include *.py -Recurse -Pattern '^\s*(from|import)\s+(apps|config|gateway|shared|models)\b'` 命中 0。
- [x] 3.2 将 `tests/` 内所有五个顶层前缀改为 `backend.*`，`engines` 相关测试不动；验证：`Select-String -Path tests -Include *.py -Recurse -Pattern '^\s*(from|import)\s+(apps|config|gateway|shared|models)\b'` 命中 0。
- [x] 3.3 将 `utils/` 内对五个顶层包的 import / settings 字符串改为 `backend.*`；验证：`Select-String -Path utils -Include *.py -Recurse -Pattern '^\s*(from|import)\s+(apps|config|gateway|shared|models)\b'` 命中 0。
- [x] 3.4 处理字符串引用：`settings.py` 的 `INSTALLED_APPS` / `MIDDLEWARE` / DRF 类、`config/urls.py` 的 `include()`、`shared/schema.py` 的 `target_class`、测试中的 `patch("apps...")` 与 `importlib.import_module("apps...")`；验证：全仓 `Select-String -Pattern '["''](apps|config|gateway|shared|models)\.'` 的剩余命中逐条说明（只允许历史归档/文档中的当时路径）。
- [x] 3.5 运行 `python -m ruff check --select I --fix backend tests utils` 统一 import 顺序；验证：`python -m ruff check --select I backend tests utils` 退出码 0，且 diff 只含 import 行。

## 4. Django 配置与入口

- [x] 4.1 更新 `backend/config/settings.py`：`INSTALLED_APPS` 改为 `backend.gateway`、`backend.shared`、`backend.apps.*`；`MIDDLEWARE` 改为 `backend.gateway.middleware.JWTAuthenticationMiddleware`；`ROOT_URLCONF=backend.config.urls`；`ASGI_APPLICATION=backend.config.asgi.application`；DRF 认证/渲染器改为 `backend.shared.*`；Jazzmin 图标键改为 `backend.apps.*`；验证：`python manage.py check` 能加载 settings（允许后续任务未完成前的路由错误，但不得是 `ModuleNotFoundError`）。
- [x] 4.2 更新 9 个 `apps.py` 的 `name` 为 `backend.apps.<app>`，保留既有 `label`（尤其 `accounts`）与 `verbose_name`；验证：`python manage.py check` 通过，`python manage.py showmigrations` 的 app label 列表与迁移前一致。
- [x] 4.3 更新 `backend/config/urls.py` 的 `include("backend.apps...")`、`backend/config/asgi.py` 的 `from backend.gateway.routing import websocket_urlpatterns`、`tests/test_settings.py` 的 `from backend.config.settings import *`；验证：`python manage.py check` 与 `python manage.py spectacular --validate` 通过。
- [x] 4.4 更新根 `manage.py`、`run.py`、`run_daphne.py`：`DJANGO_SETTINGS_MODULE=backend.config.settings`；`run.py` 的 `config.asgi:application` 改为 `backend.config.asgi:application`；`run.py` 顶部 `from backend.config.env import load_dotenv`；验证：`python manage.py check`、`python run.py status`、`python run_daphne.py --help` 均不报 `ModuleNotFoundError`。
- [x] 4.5 更新 `backend/shared/schema.py` 的 `target_class` 为 `backend.shared.auth.drf_auth.JWTAuthentication`；验证：`python manage.py spectacular --validate` 无 `W001 could not resolve authenticator`，`/api/schema/` 的 `securitySchemes.jwtAuth` 存在。

## 5. 路径语义与运行时数据

- [x] 5.1 在 `backend/config/settings.py` 定义 `BASE_DIR=backend/` 与 `REPO_ROOT=BASE_DIR.parent`；`TEMPLATES["DIRS"]` 指向 `BASE_DIR/templates`；`STATICFILES_DIRS` 指向 `BASE_DIR/static`；`STATIC_ROOT`、`DATA_DIR`、`LOG_DIR`、`EXPORT_DIR`、SQLite `NAME` 指向 `REPO_ROOT` 下的原位置；验证：`python -c` 打印上述路径与迁移前一致，`python manage.py check` 通过。
- [x] 5.2 更新 `backend/config/env.py` 的 `ROOT` 为仓库根（`parents[2]`），确认继续加载根 `.env`；验证：`python -c "from backend.config.env import ROOT; print(ROOT)"` 输出仓库根，`python -c "from backend.config.env import load_dotenv; load_dotenv(); import os; print(os.environ.get('DJANGO_SECRET_KEY'))"` 能读到 `.env` 值（非生产密钥只打印是否为空）。
- [x] 5.3 更新 `backend/apps/report_generator/service.py` 的 `BASE_DIR` 为仓库根（`parents[3]` 或 `settings.REPO_ROOT`），确保 `logs/` 与 `exports/` 仍在仓库根；验证：`python -c "from backend.apps.report_generator.service import LOG_DIR, EXPORT_DIR; print(LOG_DIR, EXPORT_DIR)"` 指向仓库根。
- [x] 5.4 验证模板/静态资源：`backend/templates/drf_spectacular/swagger_ui.html` 与 `backend/static/` 存在，`/api/swagger/` 启动后返回 200 且页面不是 drf-spectacular 默认主题；验证：启动后端后 `Invoke-WebRequest http://127.0.0.1:8766/api/swagger/` 状态码 200，HTML 含 `animal-island` 或自定义 CSS 标记。

## 6. 工具链与 CI

- [x] 6.1 更新 `tests/pytest.ini` 的 `DJANGO_SETTINGS_MODULE=tests.test_settings`；`ruff.toml` 的 `known-first-party` 改为 `["backend", "engines", "utils"]`，`per-file-ignores` 的 `config/settings.py` 改为 `backend/config/settings.py`，`tests/test_settings.py` 保持不变；`pyproject.toml` 的 `coverage.run.source=["backend/apps"]`；验证：`python -m pytest -c tests/pytest.ini --collect-only -q` 与 `python -m ruff check backend` 不因配置报错。
- [x] 6.2 更新 `utils/check_gates.py`：`PY_SCOPES` 改为五个 `backend/...` 路径，`_env()` 的 `DJANGO_SETTINGS_MODULE` 改为 `backend.config.settings`；验证：`python utils/check_gates.py --only ruff-lint,ruff-format` 实际扫描到 `backend/` 文件（输出非空/无「directory not found」）。
- [x] 6.3 更新 `utils/gen_arch_stats.py` 的 `PROJECT_ROOT / "apps"` 为 `PROJECT_ROOT / "backend" / "apps"`，保留按 `apps/` 子串识别 App 的逻辑；验证：`python utils/gen_arch_stats.py --check-boundaries` 扫描到 9 个 App 且输出「零违规」。
- [x] 6.4 更新 `utils/check_openapi_coverage.py` 的 `DJANGO_SETTINGS_MODULE=backend.config.settings`；验证：`python utils/check_openapi_coverage.py` 退出码 0，OpenAPI 业务路径覆盖数与迁移前一致。
- [x] 6.5 更新 `dsh-plugins/arch-gate/src/index.ts` 的 `pathGlobs` 为 `backend/apps/**/*.py`，同步 `dsh-plugins/arch-gate/README.md` 与 `dsh-plugins/patch.yml` 中的路径说明；验证：按插件实际调用方式执行 `python utils/gen_arch_stats.py --check-boundaries`，stdout 含「零违规」且无 Traceback。
- [x] 6.6 更新 `.github/workflows/ci-phase1.yml`：`ruff format/check` 路径、安全扫描 `grep` 路径、OpenAPI 相关路径全部加 `backend/`；验证：`Select-String -Path .github\workflows\*.yml -Pattern '(^|[^a-z])apps/|(^|[^a-z])config/|(^|[^a-z])gateway/|(^|[^a-z])shared/|(^|[^a-z])models/'` 命中 0（`backend/apps/` 等允许），YAML 可被 `yaml.safe_load` 解析。
- [x] 6.7 更新 `run.py` 的 `BASE_ENV`、`start_backend()` 的 ASGI 参数与 `from backend.config.env`；验证：`python run.py check` 能启动门禁，`python run.py status` 正常输出。
- [x] 6.8 全仓工具链残留检查：`Select-String -Path . -Include *.toml,*.ini,*.yml,*.yaml,*.ts,*.mjs,*.js,*.json -Recurse -Pattern '(^|[^a-z])apps/|(^|[^a-z])config/|(^|[^a-z])gateway/|(^|[^a-z])shared/|(^|[^a-z])models/'` 的命中逐条确认；允许 `backend/...`、`openspec/changes/archive/**`、`frontend/**` 的非后端同名路径；验证：不存在仍指向旧后端目录的可执行配置。

## 7. 测试同步

- [x] 7.1 更新 `tests/` 内全部五个顶层 import 为 `backend.*`；验证：`Select-String -Path tests -Include *.py -Recurse -Pattern '^\s*(from|import)\s+(apps|config|gateway|shared|models)\b'` 命中 0，`python -m pytest -c tests/pytest.ini --collect-only -q` 无 ImportError。
- [x] 7.2 更新测试中的字符串引用：`patch("apps...")`、`importlib.import_module("apps...migrations...")`、`shared.renderers...` / `shared.auth...` 断言；验证：`Select-String -Path tests -Include *.py -Recurse -Pattern '["''](apps|config|gateway|shared|models)\.'` 命中逐条说明，`python -m pytest -c tests/pytest.ini --collect-only -q` 通过。
- [x] 7.3 更新测试中的路径断言：`REPO_ROOT / "apps"`、`REPO_ROOT / "shared"`、`parents[3] / "apps"` 等改为 `backend/...`；验证：`python -m pytest -c tests/pytest.ini tests/arch tests/graybox/unit/test_auth_frontend_contract.py tests/graybox/unit/test_enum_ssot.py -q` 通过。
- [x] 7.4 更新 `tests/arch/test_view_write_convergence.py` 与 `tests/arch/test_channels.py` 的扫描根与 `gateway` import；验证：`python -m pytest -c tests/pytest.ini tests/arch -q` 通过，且测试实际发现 `backend/apps/*/views*.py`。
- [x] 7.5 运行聚焦回归（不跑全量）：`python -m pytest -c tests/pytest.ini tests/arch tests/graybox/unit/test_env_loader.py tests/graybox/unit/test_renderer_slot.py tests/graybox/unit/test_task_model_ownership.py tests/api/test_task_submit_sop.py -q`；验证：全部通过。

## 8. 文档同步

- [x] 8.1 更新根 `AGENTS.md`、`README.md` 的目录树、命令示例与「根目录即后端」表述；验证：两文件中不再出现指向根 `apps/`、`config/`、`gateway/`、`shared/`、`models/` 的可执行命令。
- [x] 8.2 更新移动后的 `backend/apps/AGENTS.md`、`backend/apps/自测与检测指令.md` 及 9 个 App 的 `AGENTS.md` 路径引用；验证：`Select-String -Path backend/apps -Include AGENTS.md,*.md -Recurse -Pattern '(^|[^a-z])apps/'` 的剩余命中仅为 `backend/apps/` 或历史说明。
- [x] 8.3 更新 `openspec/schemas/android-autotests/templates/tasks.md` 及 `dev_docs` 中的后端路径命令；验证：模板中的 `python manage.py` / `pytest` 命令仍从仓库根执行，路径不指向已不存在的根目录。
- [x] 8.4 确认不改写 `openspec/changes/archive/**`；验证：`git status --short openspec/changes/archive` 无输出。

## 9. 验证、提交与关单

- [x] 9.1 运行 `python manage.py check`、`python manage.py makemigrations --check`、`python manage.py showmigrations`；验证：check 通过、无新迁移、app label 与迁移前一致。
- [x] 9.2 运行 `python -m pytest -c tests/pytest.ini --collect-only -q` 与第 7.5 条聚焦回归；验证：收集无 ImportError，聚焦用例全绿。
- [x] 9.3 运行 `python run.py check`；验证：阻塞项全绿，输出中 `ruff` / `pytest` / `openapi` / `boundary` 检查实际覆盖 `backend/`。
- [x] 9.4 启动后端 `python run.py restart backend`，实测 `/`、`/api/swagger/`、`/api/schema/`、登录后 `/api/tasks/`；验证：HTTP 200/401 符合预期，无 500、无 `ModuleNotFoundError`，Swagger 使用自定义模板。
- [x] 9.5 运行 `python utils/gen_arch_stats.py --check-boundaries` 与 `python utils/check_openapi_coverage.py`；验证：零违规、覆盖率与迁移前一致。
- [x] 9.6 运行 `openspec validate 2026-10-21-backend-package-layout --strict`；验证：通过。
- [x] 9.7 逐文件 `git add` 本变更文件（禁止 `git add -A`），按「目录移动 / import 与配置 / 工具链与文档」拆分提交；验证：`git status --short` 中无并发会话文件，`git log --stat` 与本变更 Impact 一致。
- [x] 9.8 推送 `Kahoku` 并确认 `ci-phase1.yml` 的 6 个 job 全绿；验证：`backend-check` / `frontend-check` / `static-checks` / `security-scan` / `boundary-check` / `frontend-quality` 全部 success；失败项当场修复后重推。
- [x] 9.9 CI 全绿后执行 `openspec archive 2026-10-21-backend-package-layout`，再跑 `openspec validate --all --strict`；验证：归档成功，全量 spec 校验通过。
