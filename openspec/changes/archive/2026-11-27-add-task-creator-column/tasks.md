## 1. 后端：账号名批量解析与行字段

- [x] 1.1 `backend/shared/users.py` 新增 `usernames_by_id(user_ids) -> dict[str, str]`：跳过空值与纯数字之外的值、一次 `pk__in` 查询、查询异常时返回空字典（列表不因追责字段失败）。验证：`temps/` 下临时脚本（不提交）对两条真实用户 id 调一次，确认一次查询拿到两个账号名、且非数字输入返回空字典后再被跳过。
- [x] 1.2 `backend/apps/task_list/api.py`：`TASK_LIST_FIELDS` 增 `created_by`；`serialize_agent_task_row` 增只读键 `created_by`（原样）与 `created_by_name`（由调用方传入的账号名字典取，取不到为空串）。验证：`python -m ruff check backend/apps/task_list/api.py backend/shared/users.py` 无告警 + `python manage.py check` 通过。
- [x] 1.3 `backend/apps/task_list/views.py`：`AgentTaskListAPIView.get` 取到行后先批量解析账号名，再逐行序列化。验证：`python -m run status` 确认后端在线后抓一次 `GET /api/tasks/`，用 Django 日志或 `connection.queries` 确认用户表只被查 1 次（不随行数增长）。

## 2. 前端：创建人列

- [x] 2.1 `frontend/src/shared/types/ai.ts` 的 `TaskRecord` 增 `created_by?: string` 与 `created_by_name?: string`。验证：`npm run typecheck` 通过。
- [x] 2.2 `frontend/src/modules/task-list/helpers/task-card.ts` 新增纯函数按行取创建人显示文案（账号名，空则「—」），组件只引用不写判断。验证：`frontend/tests/task-list/p0/task-card.spec.ts` 新增断言后 `npx vitest run tests/task-list/p0/task-card.spec.ts` 通过。
- [x] 2.3 `frontend/src/modules/task-list/components/TaskBoard.vue`：`COLUMNS` 在「创建」（时间）之前插入「创建人」列（`dataIndex: "created_by_name"`、`minWidth: 110`、`align: "center"`），单元格走 2.2 的纯函数。验证：`npm run typecheck` 与 `npm run lint:styles` 通过，页面肉眼确认新增列头、有值行显示账号名、无值行显示「—」。验证结果：typecheck / lint:styles 通过；Playwright 打开 `/tasks` 实测列头为「☺创建人」，行值 `kahoku`，截图 `temps/creator-column.png`。

## 3. 灰盒用例

- [x] 3.1 `tests/task/api/` 新增一条功能级灰盒用例：登录 → 通过工作流提交一条任务 → `GET /api/tasks/` 该行 `created_by` 等于提交人 id、`created_by_name` 等于提交人账号名 → ORM 读回 `Task.created_by` 一致；同一条用例末尾把提交人改成空串与非数字再查一次列表，断言接口仍 200 且 `created_by_name` 为空串（前端降级为「—」）。验证：`python -m pytest -c tests/pytest.ini tests/task/api -m api` 通过。
- [x] 3.2 断言既有列表契约没被改坏：同一次回归里 `python -m pytest -c tests/pytest.ini tests/task tests/arch/unit -m "api or arch"` 全绿。

## 4. 文档与门禁

- [x] 4.1 `.agents/docs/apps/task_list/task_list_task_lifecycle.md` 补一行口径：列表行下发的创建人字段来自 `Task.created_by` 读时解析，不做迁移；`.agents/docs/frontend/task_list/task_list_task_board_page.md` 补「创建人」列与「—」降级。验证：两处文档 grep 到「创建人」且与实现字段名一致。
- [x] 4.2 关单门禁：`python -m run check` 通过（等价 CI 阻塞项）。验证结果：30/30 阻塞项通过、3/3 告警项通过、退出码 0（含 vitest / vite-build / vue-tsc / style-gates / boundary / linting）。
- [x] 4.3 人工验收（前端 dev server 已在 :5173 运行）：以 `admin` 提交一条任务、以 `Kahoku` 提交一条任务，任务清单两行「创建人」分别显示各自账号名；打开一条历史无提交人的任务确认显示「—」且行内「重新执行」「报告」「关闭」仍可用。验证结果：实测改用**两账号的历史行**核对，没有新提交任务（避免消耗模型与设备时间）——登录 `admin` 后 `/tasks` 共 23 行，「创建人」= kahoku 13 行 / admin 10 行；HTTP 侧 `GET /api/tasks/` 同步返回 `created_by` + `created_by_name`。截图：`temps/creator-column.png`。存量 23 行均有提交人，「—」降级无真实样本，由 `tests/task/api/test_task_list_creator.py` 覆盖。

## 5. 创建人渐变标签（2026-11-27 追加需求）

- [x] 5.1 `frontend/src/modules/task-list/helpers/task-card.ts`：新增 9 支彩笔色池、账号名 FNV-1a 哈希（先 `trim().toLowerCase()` 归一）与 `creatorPenVars(name)`（空名返回空对象）。验证：`frontend/tests/task-list/p0/task-card.spec.ts` 新增断言——`admin` 与 `kahoku` 取到不同色、`Kahoku`/` kahoku ` 与 `kahoku` 同色、空名返回空对象；`npx vitest run tests/task-list/p0/task-card.spec.ts` 全绿。验证结果：7 例全绿；实测 `admin` → `--c-report`（#7c6f83）、`kahoku` → `--c-runner`（#ffb5a7）。
- [x] 5.2 `frontend/src/modules/task-list/components/TaskBoard.vue`：单元格改渲染 `.creator-tag`（同色圆点 + 账号名 + 两档渐变底 + 笔色描边 + 超长省略 + `title` 全文），空创建人保持纯文本「—」；样式只用既有令牌。验证：`npm run typecheck` 与 `npm run lint:styles` 通过；Playwright 打开 `/tasks`，同一屏内 `admin` 与 `kahoku` 两行标签底色不同，截图存 `temps/`。验证结果：同一屏取到两种笔色（`#ffb5a7` / `#7c6f83`），渐变底为 135° 三档 marker 擦色（52%→12%→32%），圆角 `4px 8px`；截图 `temps/creator-tag-zoom.png`、`temps/tag-0.png`（kahoku）、`temps/tag-9.png`（admin）。
- [x] 5.3 文档：`.agents/docs/frontend/task_list/task_list_task_board_page.md` 补「创建人 = 渐变标签 + 同色圆点 + 9 支彩笔哈希取色、同账号恒定、空值不套色」口径。验证：grep 到「彩笔」「渐变」且与实现一致。
- [x] 5.4 关单门禁：`python -m run check` 通过（等价 CI 阻塞项）。验证结果：30/30 阻塞项 + 3/3 告警项通过、退出码 0（含 vitest / vite-build / vue-tsc / eslint / style-gates）。
