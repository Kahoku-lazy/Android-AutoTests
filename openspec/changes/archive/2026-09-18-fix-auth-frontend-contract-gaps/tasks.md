## 1. 前端修正

- [x] 1.1 删除 `frontend/src/shared/types/auth.ts` 中 `AuthTokenData` 的 `user?` 字段
      （未被消费，且形状随 login/register 不同）。
  **验证**：`cd frontend && npx vue-tsc --noEmit` 的错误数不超过既有基线 30 条。
- [x] 1.2 `frontend/src/shared/api-auth-interceptors.ts`：401 分支增加公开端点豁免
      （`/auth/login`、`/auth/register`、`/auth/refresh`），命中则直接拒绝、不进入刷新流程。
  **验证**：`cd frontend && npx vue-tsc --noEmit` 不引入新错误；`cd frontend && npx vite build` 通过。

## 2. 对拍守护

- [x] 2.1 新增 `tests/graybox/unit/test_auth_frontend_contract.py`：
      （a）前端 DTO 声明的字段集合 ⊆ 后端对应响应的 key 集合（`AuthTokenData` 对 login 与 register、
      `AuthRefreshData` 对 refresh、`MeUser` 对 me 的 `user` 对象）；
      （b）拦截器公开端点清单 == 网关 `PUBLIC_PREFIXES` 中 `/api/auth/` 子集。
  **验证**：`python -m pytest tests/graybox/unit/test_auth_frontend_contract.py -v` 全绿。
- [x] 2.2 注入假项证明守护会失败：在 DTO 里临时加 `nickname?: string`、在豁免清单里临时加 `/auth/foo`，
      确认两组断言分别失败，随后**还原**。
  **验证**：注入期间对应断言失败且错误信息列出差异；还原后
      `git diff -- frontend/src/shared/types/auth.ts frontend/src/shared/api-auth-interceptors.ts` 只含 1.1 / 1.2 的预期改动。

## 3. 文档同步

- [x] 3.1 更新 `tests/AGENTS.md` §契约对拍测试：断言条数由三条改为四条，补上
      `auth-response-shape`（认证 DTO 与响应形状一致）与 `auth-session` 的公开端点清单对拍，
      并把新模块名加入文件列表。
  **验证**：该节列出的文件名与能力路径与实现一致（文件存在、能力路径存在于 `openspec/specs/`）。

## 4. 门禁

- [x] 4.1 单元与架构测试全绿。
  **验证**：`python -m pytest tests/graybox/unit tests/arch -q`（基线 325 passed，+本变更新用例）。
- [x] 4.2 新增测试文件静态检查通过。
  **验证**：`python -m ruff check` 与 `python -m ruff format --check` 对
      `tests/graybox/unit/test_auth_frontend_contract.py` 均无输出。
- [x] 4.3 前端类型检查与构建不回归。
  **验证**：`cd frontend && npx vue-tsc --noEmit` 错误数 ≤ 30；`cd frontend && npx vite build` 成功。
- [x] 4.4 登录链路端到端回归。
  **验证**：`$env:TEST_ADMIN_PASSWORD='admin123'; python -m pytest tests/e2e/test_example_e2e.py -q` 通过。
