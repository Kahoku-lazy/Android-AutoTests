## 1. 写口

- [x] 1.1 `backend/apps/accounts/api.py` 新增 `set_operator(user_id, enabled)`：组不存在则 `get_or_create`，授予走 `groups.add`、取消走 `groups.remove`，已是目标状态时不写库，目标不存在抛 `ValueError`。验证：`tests/auth/api/test_account_writes.py` 新增授予、取消、幂等、未知账号四个用例通过。

## 2. 运营接口

- [x] 2.1 `backend/apps/ops_console/api.py` 新增 `grant_operator` / `revoke_operator`：先要求操作者是超管，再拒绝自己与超管目标，通过后调 `accounts.api.set_operator` 并记日志（只记操作人与目标）。验证：`tests/ops_console/api/test_ops_grant_operator.py` 覆盖超管授予 200、运营授予 403、对自己 403、对超管 403、重复授予幂等。
- [x] 2.2 `views.py` 与 `urls.py` 增加 `POST /api/ops/users/<id>/grant-operator/` 与 `.../revoke-operator/`，先过 `_require_operator` 再进 api。验证：未登录 401、普通用户 403，`python manage.py check` 无 issues。
- [x] 2.3 改 `backend/apps/ops_console/AGENTS.md` 红线：由「禁止新增授予运营的端点」改为「授予/取消仅超管、仅这一档，写库必须经 `accounts.api.set_operator`」。验证：该文件 diff 与端点实现在同一提交内。

## 3. 前端

- [x] 3.1 `frontend/src/modules/ops-console/api.ts` 增加授予与取消两个调用，路径带尾斜杠。验证：`cd frontend && npx vue-tsc --noEmit` 通过。
- [x] 3.2 抽屉对超管显示「设为运营」或「取消运营」（随目标身份切换），运营不渲染这两个按钮；列表页提交前 `ElMessageBox` 确认，取消不发请求。验证：`frontend/tests/ops-console/` 新增按钮可见性用例通过。
- [x] 3.3 前端格式与类型：`cd frontend && npx prettier --check` 覆盖本次改动文件，`npx eslint src/modules/ops-console` 通过。

## 4. 契约与收尾

- [x] 4.1 重生成契约基线：`python manage.py spectacular --file openspec/openapi.yaml --validate --fail-on-warn`，随后 `python utils/check_gates.py --only openapi-schema,openapi-coverage` 通过。
- [x] 4.2 后端回归：`python -m pytest -c tests/pytest.ini tests/ops_console tests/auth/api/test_account_writes.py` 全绿。
- 【已取消 · 人工验收不做】4.3 人工验收：超管在抽屉把一个测试账号设为运营，该账号重新登录后侧栏出现「运营」；再取消，该账号访问 `/api/ops/users/` 返回 403。用运营账号确认抽屉里没有授权按钮。接口与按钮可见性已由测试覆盖，这一步留待页面上点一次确认。
