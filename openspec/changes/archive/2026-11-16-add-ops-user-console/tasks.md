## 1. 身份判定与账号写口

- [x] 1.1 `backend/shared/users.py` 新增 `is_operator(user_id)`：组名常量 `OPERATOR_GROUP = "运营"`，判定 = `is_superuser OR 属于该组`；空值/非数字返回 False。验证：`python manage.py check` 通过，`is_operator(None)` 输出 `False`。
- [x] 1.2 `backend/apps/accounts/api.py` 新增 `set_user_active(user_id, active)` 与 `set_user_password(user_id, new_password)`：`set_password` 落哈希、`update_fields` 限定写入、目标不存在抛 `ValueError`。验证：`tests/auth/api/test_account_writes.py` 5 个用例通过。

## 2. 后端运营接口

- [x] 2.1 新建 `backend/apps/ops_console/`（`apps.py` / `urls.py` / `views.py` / `api.py` / `serializers.py` / `AGENTS.md`），注册 `INSTALLED_APPS` 与 `config/urls.py`（前缀 `/api/ops/`）。验证：`manage.py check` 无 issues；未带令牌请求 `GET /api/ops/users/` 返回 401。
- [x] 2.2 `GET /api/ops/users/`：分页（默认 20、上限 100）、`keyword`（用户名/邮箱）、`active` 三态筛选、每行带 `identity`（`superuser`/`operator`/`user`），响应 `{users,total,page,page_size}` 且不含密码。验证：`tests/ops_console/api/test_ops_user_access.py` 8 个用例通过。
- [x] 2.3 `POST /api/ops/users/<id>/disable|enable/`：幂等；停用超管、停用其他运营、停用自己一律 403 且目标不变。验证：`test_ops_user_toggle.py` 8 个用例通过。
- [x] 2.4 `POST /api/ops/users/<id>/reset-password/`：`secrets` 生成 16 位（剔除 `0O1lI`）一次性密码，只在该响应返回；运营重置超管/其他运营/自己 403；日志不记密码。验证：`test_ops_reset_password.py` 7 个用例通过。
- [x] 2.5 不提供删除：`/api/ops/users/<id>/` 与 `/api/ops/users/<id>/delete/` 无路由，`api.py` 无 delete 写口。验证：`test_ops_no_delete.py` 通过。
- [x] 2.6 `/api/auth/me/` 补 `is_operator`；`MeUser` DTO 同步（`frontend/src/shared/api/auth.ts`）。验证：`tests/arch/unit/test_auth_frontend_contract.py` 5 个用例通过（DTO ↔ 响应一致）。
- [x] 2.7 `tests/ops_console/` 覆盖 401 / 403 / 四条边界 / 幂等 / 敏感字段缺失。验证：`python -m pytest -c tests/pytest.ini tests/ops_console tests/auth/api/test_account_writes.py` → 32 passed。
- [x] 2.8 重生成契约基线：`python manage.py spectacular --file openspec/openapi.yaml --validate --fail-on-warn`；`check_gates --only openapi-schema,openapi-coverage` 两项 PASS。

## 3. 前端运营后台模块

- [x] 3.1 模块色：复用调色板 `--color-orange-37`，新增语义别名 `--c-ops`（`tokens.css`），并登记到 doodle-craft 的 `SKILL.md` 与 `references/tokens.md`（8 支 → 9 支彩笔）。验证：`lint:styles` 对本次新增文件 0 违规。
- [x] 3.2 身份状态：**复用** `shared/composables/useAuthUser.ts`，补 `isOperator` / `ensure()` / `resetAuthUser()`（未新建第二个当前用户缓存，见 design D8）。验证：`vue-tsc --noEmit` 通过。
- [x] 3.3 新建 `frontend/src/modules/ops-console/`（`index.vue` / `routes.ts` / `api.ts` / `types.ts` / `constants.ts` / `index.style.css` / `components/OpsUserDrawer.vue` / `composables/useOpsUsers.ts` / `AGENTS.md`），在 `router.ts` 注册 `/ops/users`。验证：`vue-tsc --noEmit` 通过、`vite build` 通过。
- [x] 3.4 列表页：`WorkbenchHeader` + `FilterTabs`（全部/启用/停用）+ 搜索框 + `AppTable` 表纸 + 服务端分页工具条；三态用 `SkeletonCard` / `ErrorState` / `EmptyState`，加载期不渲染空态。验证：`npm run lint:styles`（新增文件 0 违规）、`vue-tsc --noEmit` 通过。
- [x] 3.5 右侧抽屉：账号信息 + 身份/状态标签 + 停用/启用 + 重置密码，两个动作都走 `ElMessageBox` 二次确认（停用文案写明 1 小时令牌余量），重置后展示一次性密码。验证：`frontend/tests/ops-console/p0/ops-users.spec.ts` 通过。
- [x] 3.6 侧栏在「AI任务」之后追加「运营」分组（`requiresOperator`），仅运营可见；非运营深链由 `router.ts` 守卫拦回 `/dashboard`。验证：`ops-nav.spec.ts` 6 个用例通过。
- [x] 3.7 前端门禁：`eslint`、`vue-tsc`、`prettier`（本次改动文件）、`vitest`（ops-console 12 passed）全绿。

## 4. 收尾

- [x] 4.1 本地门禁 `python run.py check`：**23/25 阻塞项通过**（第 3 轮复核仍为同一结果）。剩余 2 项（`pytest-collect`、`engines-agents-retirement`）由**同一个未跟踪文件** `tests/engines/backend_bridge/unit/test_model_billing_parity.py` 触发——它第 13 行仍 `from engines.agents.messaging.billing import DeepSeekBilling`，而 `engines/agents/` 在 HEAD 上已被整体删除。该文件属并发进行中的 `retire-engines-agents` 收尾（同目录的 `test_model_billing.py`、`test_import_guard.py` 也在被持续修改，三轮间内容不同、收集数 777→779），**未擅自删改他人在途文件**，故本项保持未勾并已把目标标记为阻塞。
  - 本变更自身验证（第 3 轮复核，全部对当前工作区重跑）：`tests/ops_console` + `tests/auth/api/test_account_writes.py` + `tests/arch/unit/test_auth_frontend_contract.py` → **39 passed**；前端 `tests/ops-console` → **12 passed**；`vue-tsc --noEmit` 无输出。
- [x] 4.2 人工验收：**浏览器实测已完成，未改任何真实账号数据**。
  - 运营视角（超管 `admin`，见 `temps/ops_page_probe.py`）：`/ops/users` 渲染 20 行 / 20 身份标签 / 20 状态标签，侧栏「运营 · 用户管理」可见，计数「共 212 个账号」，分页「第 1/11 页 → 第 2/11 页」，抽屉可开且 2 个动作就位，**控制台 0 错误**；截图 `temps/ops-users.png`、`temps/ops-users-drawer.png`。
  - 防呆（`temps/ops_ui_guard_probe.py`）：超管行 `admin` 的两个动作**均置灰**并显示「超级管理员账号不能被停用或重置密码」；普通用户行点「停用账号」只弹二次确认，**按 Esc 取消后写请求 0 次**；截图 `temps/ops-superuser-guard.png`、`temps/ops-confirm-dialog.png`。
  - 越权（`temps/ops_rbac_probe.py`，用 e2e 套件的 `e2e_probe` 账号）：`GET /api/ops/users/` → **403**「仅运营可访问运营后台」；侧栏「运营」分组与「用户管理」项**均不出现**；深链 `/ops/users` 被弹回 `/dashboard`，全程 `/api/ops/` 请求 **0 次**，控制台 0 错误。
  - **仍待需求方亲测**：真点一次「停用 / 重置密码」（会改真实账号），该写路径目前由测试库 32 个用例覆盖。
- 【已取消 · 未做取消】4.3 逐文件 `git add`（禁止 `-A`）并提交，推送 `Kahoku`，确认 `ci-phase1.yml` 6 个 job 全绿。建议拆两个提交：`feat(ops): 运营后台用户管理页`、`style(case-manager): 按 prettier 格式化 ProjectWorkspace.vue`。
- [x] 4.4 归档：`/opsx:archive add-ops-user-console`，把 `ops-user-console` 的 delta 合入主 spec。

## 5. 门禁红项（本变更之外，逐条留证）

| 门禁 | 状态 | 原因 | 归属 |
| --- | --- | --- | --- |
| `prettier` / `prettier-ts` | **已解决** | `case-manager/api.ts` 只是 CRLF 换行（git 视角零差异）；`ProjectWorkspace.vue` 有 1 行真实格式差异，已用 lockfile 版本 `prettier@3.9.4 --write` 修正 | 本单附带，单列 `style(case-manager):` 提交 |
| `pytest-collect` | 红 | 未跟踪文件 `tests/engines/backend_bridge/unit/test_model_billing_parity.py` 导入已删除的 `engines.agents.messaging.billing` | `retire-engines-agents`（33/35，收尾中；同目录另有未跟踪的 `test_model_billing.py`） |
| `engines-agents-retirement` | 红 | 同一文件命中「下线面无残留」扫描 | 同上 |
| 旁证（不在阻塞项内） | 红 | HEAD 上 `tests/arch/unit/test_channels.py` 仍断言 `engines/agents` 目录存在；`tests/bug_ticket/unit/test_bug_ticket_log_interrupt.py` 在 HEAD 上仍导入 `engines.agents.tools.tool_serial`（本地已被并发改动修掉，表现为 `M`） | 同上 |
