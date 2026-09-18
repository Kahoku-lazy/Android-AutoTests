## 1. 令牌配置（D0）

- [x] 1.1 `config/settings.py` 新增 `AI_TOOL_GATEWAY_TOKEN = os.environ.get("AI_TOOL_GATEWAY_TOKEN", "")`（放在 JWT 配置之后、DRF 配置之前，附「留空 = 该前缀一律 401（fail-closed）」注释）
- [x] 1.2 `.env.example` 新增该键（含 `python -c "import secrets; print(secrets.token_urlsafe(32))"` 生成命令与 fail-closed 说明）

## 2. 通道校验（D1）

- [x] 2.1 新增 `gateway/internal_token.py::InternalToolTokenMiddleware`：仅当路径以 `/api/ai/tools/` 开头且非 `OPTIONS` 时校验 `X-Internal-Token`（`HTTP_X_INTERNAL_TOKEN`），`hmac.compare_digest` 常量时间比较；失败 401 + `{"status": false, "message": "内部令牌无效"}`（统一文案，不暴露「未配置」还是「不匹配」）；其余请求直接 `get_response` 放行
- [x] 2.2 `config/settings.py` MIDDLEWARE：插在 `corsheaders.middleware.CorsMiddleware` 之后、`django.middleware.security.SecurityMiddleware` 之前（附注释说明只在工具网关前缀生效）
- [x] 2.3 `gateway/middleware.py` `PUBLIC_PREFIXES`：注释重写为三类理由（登录类必需公开 / `/api/ai/tools/` 免 JWT 但由内部令牌中间件保护 / API 文档面有意公开），10 条不变

## 3. 视图与文档同步

- [x] 3.1 `apps/ai_assistant/views/tool_gateway.py`：模块 docstring 改写（真相源 `apps/ai_assistant/tools.py`、鉴权 = `X-Internal-Token`、AgentScope 已进程内）；修正三处路径前缀 `/api/tools/...` → `/api/ai/tools/...`；`tool_schemas`/`tool_gateway` 视图 docstring 去掉「No authentication required」「JWT authentication is enforced by the global middleware」错误表述
- [x] 3.2 `dev_docs/05-开发与测试/接口文档/API-AI助手.md`：§1 表格 3 行鉴权列 `公开` → `内部令牌`；§2 通用约定鉴权 bullet 改为「唯一例外是工具网关 + 内部令牌机制 + 未配置即 401」；§10 标题注补「鉴权（内部令牌）」段（`X-Internal-Token` 请求头示例 + 401 错误响应 + 预检不校验）；§10.1/10.2/10.3 三处 `| 鉴权 | 公开（服务间） |` → `| 鉴权 | 内部令牌（X-Internal-Token） |`（`replace_all`）。验证：文档内「公开（服务间）」残留 **0** 行
- [x] 3.3 `apps/AGENTS.md` §2：公开路径清单由「3 条」改为指向唯一真相源 `gateway/middleware.py::PUBLIC_PREFIXES`，并逐类列出（登录类 / 已退役鉴权路径 / 后台与静态 / API 文档面有意公开 / 工具网关内部令牌）

## 4. 验证

- [x] 4.1 新增 `tests/graybox/unit/test_ai_tool_gateway_auth.py`（`pytestmark = [django_db, unit, ai_assistant]`，7 例）→ **7 passed**：无令牌 401 / 错误令牌 401 / 正确令牌 200（`devices/list_all`，body `{"status": true, "data": []}`）/ 令牌未配置 401（fail-closed）/ 业务端点仍 401 / 文档端点仍 200 / OPTIONS 预检非 401
- [x] 4.2 回归对照组：同文件内 `GET /api/devices/` → 401、`GET /api/docs` → 200、`GET /api/schema/` → 200（均已断言通过）
- [x] 4.3 CORS 预检：`OPTIONS /api/ai/tools/devices/list_all` + `Origin` + `Access-Control-Request-Method` → 断言 `!= 401` 通过（中间件显式跳过 OPTIONS，且排在 corsheaders 之后）
- [x] 4.4 `python manage.py check` → **0 issues**；`python -m ruff check gateway config apps/ai_assistant tests/...` → **All checks passed**（新增 2 文件已 `ruff format`）；`python -m pytest -m "unit or integration"` → **1 failed, 72 passed, 46 deselected**（唯一失败为既有 `test_case_manager_ids::test_next_case_id_increments_same_day`，与本变更无关；新增 7 例全过）
- [x] 4.5 `python tools/gen_arch_stats.py --check-boundaries` → **零违规**
- [x] 4.6 `openspec validate secure-ai-tool-gateway --strict` → **Change is valid**

## 5. 遗留说明

- 本变更未改 `config/settings.py` 既有格式问题（`JAZZMIN_SETTINGS.icons` 缩进使 `ruff format --check config/settings.py` 失败）——已核实 `--diff` 只含该既有行，属 `cleanup-d0-consistency` 单，未夹带。
