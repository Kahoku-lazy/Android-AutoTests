## 1. #4 失效的 custom_css

- [x] 1.1 `config/settings.py` 删除 `JAZZMIN_SETTINGS["custom_css"] = "css/admin-fonts.css"` 及其注释行（该文件从未存在，键从未生效）
- [x] 1.2 验证：`custom_css` 全仓残留 **0**；`Client().get("/admin/login/")` → 200 且响应中**不再包含** `admin-fonts.css`（修复前为 True）；`manage.py check` 零 issues

## 2. #5 日志配置生效

- [x] 2.1 `config/settings.py`：`LOGGING` 改为**无条件定义** —— 本地档位 `console` + `logs/django.log`（`RotatingFileHandler` 5MB×3，`delay=True` 防目录未建）；容器档位（`DOCKER_CONTAINER`）只留 `console`（stdout）；根与 `django`/`daphne` logger 级别读 `LOG_LEVEL`（默认 `INFO`）
- [x] 2.2 `.env.example` 新增 `LOG_LEVEL` 与 `DOCKER_CONTAINER` 说明
- [x] 2.3 验证：新增 `tests/graybox/unit/test_logging_config.py`（5 例）→ **5 passed**（根 handler 非空且级别匹配 `LOG_LEVEL`、本地档位含 file handler 且指向 `logs/django.log`、`django`/`daphne` logger 显式配置且 `propagate=False`、运行时根 logger 确有 handler、应用级 INFO 记录不被丢弃）；容器档位实测：`DOCKER_CONTAINER=true` → `handlers = ['console']`（无 file handler）

## 3. #6 API 文档一致性

- [x] 3.1 修正 `config/api_docs.py` 已失效内容：**删除 WebSocket 模块块**（`/ws/screenshot` 及其响应示例，WS 生产点现为 0）· `:439`「跨 7 个模块聚合…test_runner…」→「跨 6 个模块聚合」（去掉 test_runner）· 统计字段 `modules 6→5` · `endpoints 39→29` · `websockets 2→0` · `base_url :8765→:8766` · HTML 副标题同步 · 删除已无用的 `.m-WS` 样式与 WebSocket 过滤按钮
- [x] 3.1b **额外发现并修复 6 个「已记录但不存在」的端点**（`temps/api_docs_drift.py` 用 `resolve()` 探测，占位符按 `1`/`dummy` 容错）：`/api/elements/dump` · `/api/elements/action`（抓取类已迁至 inspector）· `/api/cases/export/yaml` · `/api/cases/exports` · `/api/cases/exports/{filename}` · `/api/cases/suites`（case_manager 已下线 YAML 导出与相关 legacy 路径，见其 `AGENTS.md`）→ 全部整块删除（70 行），并把 element-locator 模块 `desc` 注明「抓取类端点已迁至 inspector 模块」。复核：缺失数 **6 → 0**
- [x] 3.2 `config/api_docs.py` 文件头补说明：人工维护的公开文档快照 / 真相源是各 App `urls.py` 与 `/api/schema` / 只收录主要业务端点（非全量，router 展开与 admin/static/media 不在范围）/ 一致性由测试看守
- [x] 3.3 新增 `tests/graybox/unit/test_api_docs_consistency.py`（4 例）→ **4 passed**：文档 → 代码严格断言（`resolve()` 探测，容错转换器与尾斜杠）、缩水下限（模块 ≥5 / 端点 ≥25 / 分组非空）、WS 生产点为 0 时不得收录 WS、`/api/docs` 与 `/api/docs.html` 可渲染（该例需 `django_db`：JWT 中间件会调用 `close_old_connections()`）
- [x] 3.4 验证：修复 3.1b **之前**该用例确实失败并列出 6 条缺失（先留证再修），修完后通过

## 4. #7 .env 解析收敛

- [x] 4.1 新增 `config/env.py::load_dotenv(env_file=None)`（纯标准库，无 Django 依赖；语义 = 原 `settings.py::_load_dotenv`：只处理 `KEY=VALUE`、跳过空行/注释、去掉成对引号、**已存在的环境变量优先**）
- [x] 4.2 `config/settings.py` 删除 `_load_dotenv`，改 `from config.env import load_dotenv` + `load_dotenv()`
- [x] 4.3 `run.py` 删除 `_load_env`，改同一实现（`from config.env import load_dotenv`）
- [x] 4.4 验证：`settings.py`/`run.py` 中 `_load*` 定义与调用残留 **0**；新增 `tests/graybox/unit/test_env_loader.py`（5 例）→ **5 passed**（三种引号写法、真实环境变量优先、注释/空行/非法行跳过、文件不存在静默返回、值内含 `=` 只按首个切分）

## 5. 验证与关单

- [x] 5.1 `python manage.py check` → **0 issues**；`python -m ruff check` + `--format --check`（仅本单涉及文件）→ **All checks passed / 7 files already formatted**
- [x] 5.2 `python -m pytest -m "unit or integration"` → **1 failed, 94 passed, 46 deselected**（唯一失败为既有 `test_case_manager_ids::test_next_case_id_increments_same_day`，与本变更无关）
- [x] 5.3 `python tools/gen_arch_stats.py --check-boundaries` → **零违规**
- [x] 5.4 `python tools/gen_arch_stats.py --check-md` → 见前轮记录（本文无 ARCH_STATS 自动区域，只能提示初始化）
- [x] 5.5 `openspec validate fix-d0-config-drift --strict` → **Change is valid**

## 6. 与开单设计的差异 / 遗留（据实登记）

- **差异 1（测试口径）**：原任务书写「双向全量断言」。实测该文档是**精选子集**（29 个端点 vs 路由表 116 条静态条目），「路由 → 文档」全量断言会把绝大多数合法端点判为缺失。故改为：**文档 → 代码严格断言** + **缩水下限**（模块/端点下限、分组非空、WS 规则）。已在测试文件头写明该口径与理由。
- **差异 2（修复面）**：原任务书只点名 `/ws/screenshot` 与 test_runner 表述；实测另有 **6 个失效端点**（见 3.1b）一并删除，否则新加的看守用例无法通过。
- **范围外副作用**：`config/settings.py` 被 `ruff format` 整文件格式化，**包含** `JAZZMIN_SETTINGS.icons` 的缩进修复（原属 `cleanup-d0-consistency` 的 #11）。因本单必须改该文件（env loader / LOGGING），格式化属同文件副作用；`cleanup-d0-consistency` 执行时应跳过该项。
- **未动**：`README`/部署手册未描述新增的 `LOG_LEVEL`/`DOCKER_CONTAINER`（`.env.example` 已覆盖）；`/api/docs` 改由 drf-spectacular 渲染仍待 `complete-openapi-schema` 单完成后评估。
