## 1. 守护测试（先跑红）

- [x] 1.1 新增 `tests/graybox/unit/test_frontend_api_paths.py`：扫描 `frontend/src/**/*.{ts,vue}` 中作为 `.get` / `.post` / `.put` / `.patch` / `.delete(` 与 `fetch(` 首个参数出现的 `/` 开头字面量，逐条拼上 `baseURL=/api` 后调用 `django.urls.resolve()`；断言「带尾斜杠」且「能命中」；例外白名单仅含前端自身路由 `/login`、`/dashboard` 且写死在测试内。
  **验证**：`python -m pytest tests/graybox/unit/test_frontend_api_paths.py -v` —— 此时**预期红**，失败项应精确列出 `frontend/src/shared/api/auth.ts` 的 4 条与 `frontend/src/shared/api-client.ts:33` 的 1 条。
- [x] 1.2 新增 `tests/graybox/unit/test_auth_endpoint_declaration.py`：经 URL conf 解析取得 `apps/accounts` 的全部 APIView（不直接 import 视图模块），断言 `permission_classes` 含 `AllowAny` 当且仅当 `authentication_classes` 为空。
  **验证**：`python -m pytest tests/graybox/unit/test_auth_endpoint_declaration.py -v` 全绿（现状 5 个端点已满足该不变量，不应有失败）。

## 2. 修正认证链路路径字面量

- [x] 2.1 `frontend/src/shared/api/auth.ts`：`login` / `register` / `logout` / `me` 四处路径字面量补尾斜杠。
  **验证**：1.1 的测试中这 4 条转绿。
- [x] 2.2 `frontend/src/shared/api-client.ts:33`：`refreshRequest` 的 `/api/auth/refresh` 补尾斜杠。
  **验证**：`python -m pytest tests/graybox/unit/test_frontend_api_paths.py -v` 全绿，无失败项。

## 3. 端到端确认

- [x] 3.1 对运行中的后端逐条确认 5 个端点按前端写法命中：`login/` → 400/401、`register/` → 400、`refresh/` → 401、`logout/` → 401、`me/` → 401，均不再是 404。
  **验证**：`python temps/login-stack-map/probe_live_auth.py` 输出中 5 条带斜杠形式全部非 404。
- [x] 3.2 真实浏览器走一次登录并进入仪表盘。
  **验证**：`TEST_ADMIN_PASSWORD=<凭据> python -m pytest tests/e2e/test_example_e2e.py -v` 通过；若凭据不可得，记录为「未执行」并在关单结论中标注，不得以静态结果替代。

## 4. 文档与产物同步

- [x] 4.1 `tests/AGENTS.md` 新增一节，记录「测试读取前端源码做契约对拍」这一范式的边界（只读、只做路径一致性断言、不反向影响前端产物）与两个新测试文件的职责。
  **验证**：该节存在且与文件内既有章节体系一致。（注：`python tools/gen_arch_stats.py --check-md` 当前输出「ARCH-00-平台总体架构.md 不存在」，不构成本节的校验手段。）
- [x] 4.2 重跑登录链路关联图产物。
  **验证**：`python temps/login-stack-map/collect_stack_facts.py` 后 `node temps/login-stack-map/login-stack-map.cjs`，C 节判定由「实际 404」变为「命中」；`node temps/login-stack-map/login-stack-map.cjs --check` exit 0；`node temps/login-stack-map/verify-stack-map.cjs` 无失败项。

## 5. 门禁

- [x] 5.1 单元与架构测试全绿。
  **验证**：`python -m pytest tests/graybox/unit tests/arch -q`（基线 307 passed，加上本次新增用例）。
- [x] 5.2 架构红线零违规。
  **验证**：`python tools/gen_arch_stats.py --check-boundaries`（基线零违规）。
- [x] 5.3 前端类型检查不引入新错误。
  **验证**：`cd frontend && npx vue-tsc --noEmit` 的错误数不超过既有基线 30 条（27 在 tests/dashboard、3 在 case-manager/components/ProjectTree.vue）。
- [x] 5.4 新增测试文件的静态检查通过。
  **验证**：`python -m ruff check tests/graybox/unit/test_frontend_api_paths.py tests/graybox/unit/test_auth_endpoint_declaration.py` 与 `python -m ruff format --check` 均无输出。
