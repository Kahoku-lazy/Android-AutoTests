## 1. 侧栏入口

- [x] 1.1 在「AI任务」分组最前增加「任务清单」，路径 `/tasks`。不新建页面。验证：侧栏第一项文案与路径符合 `frontend-sidebar-nav` delta，`/tasks` 只高亮这一项。

## 2. 任务卡类型

- [x] 2.1 任务卡按 `task_kind` 显示三类：`assistant_sop` 为「SOP」，`case_authoring` 为「用例编写」，其余为「设备执行」。验证：`cd frontend && npx vitest run tests/task-list` 覆盖这三支。

## 3. 成功链接

- [x] 3.1 工作流任务提交成功后留在助手页，提示中提供进入 `/tasks` 的链接。未点击时不跳转。提交字段不变。验证：`cd frontend && npx vitest run tests/ai-assistant` 断言提示含链接且当前路由不变。

## 4. 收口

- [x] 4.1 跑前端检查。验证：`cd frontend && npx vue-tsc --noEmit` 与相关 vitest 通过。
