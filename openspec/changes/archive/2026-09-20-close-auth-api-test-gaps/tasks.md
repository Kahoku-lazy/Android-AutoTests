## 1. 用例落地（YAML）

- [x] 1.1 `tests/api/case/login.yaml` 补 TC-LOGIN-015（账号前后带空格 → 401）、016（密码前后带空格 → 200）、017（JSON 数组 → 400）、018（不带 Authorization → 200）；验证：`python -m pytest tests/api/test_login_page.py -k TC-LOGIN -q` 全绿（13 条）。
- [x] 1.2 `tests/api/case/register.yaml` 补 TC-REG-021（用户名前后带空格 → 200，入库为 strip 后的值）、022（邮箱前后带空格 → 200）；验证：`-k TC-REG` 全绿（12 条，另 1 条并发在 1.7）。
- [x] 1.3 新增 `tests/api/case/refresh.yaml`（TC-REFRESH-001/002/003/004/005，其中 004 带 `setup: logout`）、`logout.yaml`（TC-LOGOUT-001/002/003/004）、`me.yaml`（TC-ME-001/002/003）；验证：`python -c "from tests.api.loader import load_cases; [print(f, len(load_cases(f))) for f in ('refresh.yaml','logout.yaml','me.yaml')]"` 能加载且条数正确。
- [x] 1.4 `tests/api/conftest.py` 新增 `admin_tokens` fixture（现场登录种子账号，返回 access/refresh）；验证：占位符 `{{admin_refresh_token}}` 能解析（由 1.5 的用例证明）。

## 2. 驱动与流程用例

- [x] 2.1 新增 `tests/api/test_auth_tokens.py`：加载 refresh/logout/me 三个 YAML，按 `auth` 分流 session，跳过带 `setup` 的用例；验证：`python -m pytest tests/api/test_auth_tokens.py -v` 全绿。
- [x] 2.2 新增 `tests/api/test_auth_session_flow.py`：执行 4 条 `setup: logout` 用例（先登出，再断言 access 与 refresh 同时失效）；验证：`python -m pytest tests/api/test_auth_session_flow.py -v` 全绿（4 条）。
- [x] 2.3 新增 `tests/api/test_auth_register_concurrency.py`：TC-REG-023 两线程同名注册，断言 `sorted(status) == [200, 409]` 且 409 文案为「用户名已存在」；验证：连续跑 3 次均稳定通过。
- [x] 2.4 全量接口层回归 + 报告：`python -m pytest tests/api -q` 全绿（64 条，其中登录模块 39 条），并生成 `tests/reports/api.html`；验证：`64 passed in 216.32s` 且报告文件存在。

## 3. 文档同步

- [x] 3.1 `dev_docs/DEV_TEST/接口自动化测试/接口自动化测试-登录.md`：补入新增用例（五字段体例：用例名称 / 业务功能 / 测试目的 / 测试方法与步骤 / 断言逻辑），新增「认证令牌类用例（多步流程）」说明，收缩「未覆盖清单」（保留 LOGOUT-005 / ME-004 并写明归属与替代覆盖），更新规模、运行方式与报告命令；验证：文档内用例编号与 YAML 一一对应（逐条核对）。
- [x] 3.2 `dev_docs/ARCH_PRD/PRD-00-登录模块.md`：把登录 015-018、注册 021-023、刷新、登出、me 的「待设计」行迁入已实现口径（016 按实测改成 200/密码被 trim），并保留未实现的 2 条在待设计表；验证：PRD 中每条编号能与 YAML / 驱动对上。

## 4. 收尾

- [x] 4.1 后端门禁不受影响地空跑确认：`python manage.py check` + `ruff check tests/api`（本次只动 tests/）；验证：两条命令通过。
- [x] 4.2 `npx openspec validate close-auth-api-test-gaps --strict` 通过；验证：exit 0。
- [x] 4.3 归档本变更（`openspec archive`）并汇报归档路径；验证：目录出现在 `openspec/changes/archive/`。
