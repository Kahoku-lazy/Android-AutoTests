## Why

D0/D1 复检实测发现：**工具网关三个端点（schemas / agent-config / execute）无任何鉴权，未认证即可执行平台业务工具（含真机控制）**。

证据链（均可复现）：

1. `gateway/middleware.py:25`：`PUBLIC_PREFIXES` 含 `"/api/ai/tools/"`（注释写「AgentScope internal service-to-service」）→ JWT 中间件对该前缀直接放行；
2. `apps/ai_assistant/urls.py:95-97`：三条路由 `tools/schemas` · `tools/agent-config/<agent_id>` · `tools/<module>/<action>`，全在该前缀下；
3. `apps/ai_assistant/views/tool_gateway.py:28/46/120`：三个视图只有 `@csrf_exempt`，**没有任何权限/令牌校验**；`tool_gateway` 用 `resolve_by_module_action(module, action)` 拿到 handler 后直接执行，`user_id` 缺失时兜底为 `""`（`:153-157`）；
4. 该文件 `:9` 的 docstring 断言「JWT authentication is enforced by the global middleware」——与前缀豁免**自相矛盾**；
5. 实测（`temps/test_d0_probe.py`，走真实中间件链）：

   ```
   [工具网关] POST /api/ai/tools/devices/list_all  无 Authorization → 200  {"status": true, "data": []}
   [业务端点] GET  /api/devices/                    无 Authorization → 401   ← 对照组
   ```

6. 可达面 = `apps/ai_assistant/tools.py` 的 `TOOL_META` 全部 12 个工具，含 `AUTO_ALLOW_TOOLS` 里 6 个**免 HITL 的控制类**（`devices/click_ratio` · `drag_ratio` · `xpath_action` · `action` · `acquire` · `release`）；
7. 全仓**没有任何内部令牌机制**（`INTERNAL_TOKEN` / `X-Internal` / `SERVICE_TOKEN` 零命中），即当前无可用凭据可挡。

用户裁定（本次范围确认）：**工具网关改为要求内部令牌**；**`/api/docs` · `/api/schema/` · `/api/swagger/` 允许公开**（保留现状，但登记为「有意公开」）。

## What Changes

1. **新增内部令牌校验**：D1 通道层新增中间件（`gateway/`），只对 `/api/ai/tools/` 前缀校验请求头 `X-Internal-Token`，与 `settings.AI_TOOL_GATEWAY_TOKEN` 做**常量时间比较**（`hmac.compare_digest`）；不匹配 → `401`（JSON 信封，不泄露细节）。
2. **fail-closed**：`AI_TOOL_GATEWAY_TOKEN` 未配置时该前缀**一律拒绝**，不做「未配置即放开」。
3. `config/settings.py`：新增 `AI_TOOL_GATEWAY_TOKEN = os.environ.get("AI_TOOL_GATEWAY_TOKEN", "")`（凭据属 D0 外部资源根，与 `DJANGO_SECRET_KEY` 同级）。
4. `gateway/middleware.py`：`PUBLIC_PREFIXES` 保留 `/api/ai/tools/`（免 JWT），但注释改为「免 JWT，**由内部令牌中间件保护**」；同时为用户裁定的公开端点补上「有意公开」注释理由。
5. `apps/ai_assistant/views/tool_gateway.py`：修正 `:9` 的错误 docstring（改为「JWT 豁免 + 内部令牌校验」），并修正 `:3-5` 里写错的路径前缀（`/api/tools/...` → `/api/ai/tools/...`）。
6. 文档同步：`dev_docs/05-开发与测试/接口文档/API-AI助手.md`（`:63-65` 鉴权列、`:73`、`:1697-1768` 三节）由「公开」改为「内部令牌」并给出调用示例；`apps/AGENTS.md` §2 的公开路径清单与 `PUBLIC_PREFIXES`（10 条）对齐（现状只写了 3 条）；`.env.example` 增 `AI_TOOL_GATEWAY_TOKEN` 说明。
7. **BREAKING（外部调用方）**：仓库内**无任何调用方**（grep 证据：`/api/ai/tools` 仅命中白名单、视图、文档），故不影响平台自身；但任何外部/历史调用方必须补 `X-Internal-Token`，否则 401。

## 关联文档

- 契约真相源：`dev_docs/05-开发与测试/接口文档/API-AI助手.md` §10
- 代码：`gateway/middleware.py` · `apps/ai_assistant/{urls.py,views/tool_gateway.py,tools.py}` · `config/settings.py`
- 取证：`temps/test_d0_probe.py` · `temps/d0_probe_out.txt`
- 范围外登记：文档端点继续公开（用户裁定）；API schema 告警（155 条）另单

## Capabilities

### New Capabilities

（无；`openspec/specs/` 无工具网关类能力，`.openspec.yaml` 已声明 `skip_specs: true`）

### Modified Capabilities

（无）

## Impact

- **修改**：`gateway/middleware.py` · `config/settings.py` · `apps/ai_assistant/views/tool_gateway.py`（仅 docstring）· `.env.example` · `dev_docs/05-开发与测试/接口文档/API-AI助手.md` · `apps/AGENTS.md`
- **新增**：`gateway/` 内内部令牌中间件（1 个新文件）+ `tests/` 鉴权契约用例
- **不影响**：前端（无调用方）、Tool 清单、`apps/` 业务逻辑（视图执行逻辑不动）
- **测试范围**：新增用例（无令牌 401 / 错误令牌 401 / 正确令牌 200 / 业务端点仍 401 / 文档端点仍 200）· `python manage.py check` · `ruff` · `pytest -m "unit or integration"` · `--check-boundaries`
