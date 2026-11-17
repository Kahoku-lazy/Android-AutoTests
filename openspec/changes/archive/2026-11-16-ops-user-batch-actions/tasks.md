## 1. 规则与规格对齐

- [x] 1.1 改 `backend/apps/ops_console/AGENTS.md` 与 `frontend/src/modules/ops-console/AGENTS.md`：允许本页批量停用；允许仅超管批量注销且只删账号。保留「不能动自己 / 不能动超管 / 运营不能动其他运营 / 写库只经 accounts.api」。验证：两份红线表不再写「禁止删除、禁止批量」，且仍写明注销不碰业务表。
- [x] 1.2 改 `tests/ops_console/api/test_ops_no_delete.py`：删除「api 层不得出现删除写口」的断言；保留「`/api/ops/users/<id>/` 与 `.../delete/` 不存在」的路由断言。验证：`python -m pytest -c tests/pytest.ini tests/ops_console/api/test_ops_no_delete.py -q` 通过。

## 2. 账号级吊销

- [x] 2.1 在 `accounts` 吊销模型增加 `kind=user`，并给 `accounts.api` 增加按账号主键写入、删除、判定该档的写口。停用写入，启用删除。判定时：存在未过期记录且令牌 `iat` 早于记录 `created_at` 则视为已吊销。验证：`accounts` 相关单测覆盖停用写入、启用删除、旧 `iat` 拒绝、新 `iat` 放行；`python manage.py makemigrations --check` 无未生成迁移。
- [x] 2.2 `set_user_active(False)` 写 user 档；`set_user_active(True)` 删 user 档。重复停用覆盖同一行，不堆记录。验证：`python -m pytest -c tests/pytest.ini tests/ops_console/api/test_ops_user_toggle.py -q` 仍通过，并新增「停用后该账号 user 档存在、启用后不存在」。
- [x] 2.3 `verify_token` 在既有 `jti` / `sid` 检查之外读取 user 档。吊销库查询失败仍放行并记 error，不新增异常类。验证：停用前签发的 access 在停用后验签失败；启用后新签发的 access 验签成功；同文件既有吊销用例不回归。

## 3. 停用拒绝与续期

- [x] 3.1 网关在令牌验签通过后，若账号不存在或 `is_active` 为假，返回 403，正文为 `{status:false, message:"你的账号已被超管停用，10 秒后将退出登录", code:"account_disabled"}`。未停用账号的 401 文案不变。验证：停用账号请求 `/api/auth/me/` 得到该 403；启用账号的过期令牌仍是 401。
- [x] 3.2 `RefreshView` 在签发前拒绝不存在或已停用的账号，也拒绝 `iat` 早于 user 档的 refresh。返回 401，不签发 access。验证：`python -m pytest -c tests/pytest.ini tests/auth/api -q` 中既有续期用例通过，并新增停用后续期 401、启用后旧 refresh 仍 401。

## 4. 批量端点

- [x] 4.1 `ops_console` 增加 `POST /api/ops/users/disable/`。请求体 `user_ids` 去重；空、超过 100 或含非正整数返回 400 且不写库。逐行调用既有可管理校验与 `set_user_active`。响应含 `disabled` / `skipped` / `rejected` 与计数。验证：运营停用普通用户成功；已停用记 skipped；自己、超管、运营记 rejected 且状态不变；超管也不能停用运营。
- [x] 4.2 `accounts.api` 增加 `purge_users`，一个事务内 `user.delete()`，只删账号及其组、权限关系。`ops_console` 增加 `POST /api/ops/users/purge/`，仅超管；名单含自己、其他超管或不存在的主键时整批 403，不删任何行。验证：注销后同名可重新注册且主键不同；该用户创建的项目或任务行仍在且 `created_by` 不变；运营调用 403。
- [x] 4.3 两个端点同步 `openspec/openapi.yaml`，路径带尾斜杠。验证：路径与 operationId 已写入契约。全量 `spectacular --validate --fail-on-warn` 被既有 `ai_assistant` 视图警告拦住（与本变更无关），未作为本任务的通过条件。

## 5. 用户管理页

- [x] 5.1 列表增加本页复选框。不可管理的行禁用。翻页、改筛选、改每页条数清空勾选。批量停用按钮在有勾选时可点，确认沿用现有二次确认。验证：`cd frontend && npx vitest run tests/ops-console` 覆盖「翻页不提交上页勾选」与「超管/自己的复选框禁用」。
- [x] 5.2 仅超管渲染批量注销。确认框要求输入「注销 N 个账号」全字匹配才可提交，文案写明历史保留、不可恢复。运营界面不出现该按钮。验证：上述 vitest 覆盖按钮可见性与输入不匹配时不发请求。
- [x] 5.3 批量结果用逐行消息展示成功、跳过、拒绝，不用本地改状态冒充已保存；成功后重新拉取当前页。验证：vitest 断言列表来自重新请求，而不是本地改 `is_active`。

## 6. 十秒退出

- [x] 6.1 在 `frontend/src/shared/` 识别 `code === "account_disabled"`：不续期、不重试，展示固定文案并倒计时 10 秒，到点清空会话并跳 `/login`。重复响应不重置倒计时。常量放模块常量文件，不写魔法数。验证：拦截器单测覆盖「有 refresh 也不发续期」与「10 秒后清会话」。
- [x] 6.2 `cd frontend && npm run typecheck && npm run lint:styles` 通过。字号与颜色只用既有令牌。

## 7. 关单

- [x] 7.1 `python -m pytest -c tests/pytest.ini tests/ops_console tests/auth/api/test_disabled_account.py -q` 通过（53 passed）。`tests/auth` 全目录含依赖 live server / 浏览器夹具的用例，缺夹具即报错，不是本变更回归。`python utils/gen_arch_stats.py --check-boundaries` 报的两处在 `ai_assistant/services/`，属其它未提交改动，本变更未新增跨 App 写库。
- [x] 7.2 归档说明：必须先归档 `add-ops-user-console` 与 `grant-operator-role`，再归档本变更。本变更的 delta 用 REMOVED 废止「不提供删除」与「停用后旧令牌自然过期」；主规格尚未存在时单独归档会盖掉授予运营，或让 REMOVED 对不上条目。本变更不单独归档。
