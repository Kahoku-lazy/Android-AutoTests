## 1. 后端计数

- [x] 1.1 统计接口返回助手名片数、工作流数、工作流任务的 `running` / `pending` / 累计 / 今日；任务范围只含 `assistant_sop`。验证：`python -m pytest -c tests/pytest.ini tests/dashboard -q` 覆盖有名片、有工作流、有排队、有退役任务类型时的断言。
- [x] 1.2 运营与超级管理员的统计响应含 `ops.users` / `ops.agents` / `ops.models`，普通用户响应不含 `ops`，未登录仍 401。验证：同一组 dashboard 测试分三种身份断言字段有无。
- [x] 1.3 近 7 日执行柱、结果摘要、最近任务只计工作流任务；中断与取消不再映射成未执行。验证：dashboard 单测断言退役类型不进柱，`interrupted` / `cancelled` 原样出状态。
- [x] 1.4 活动接口只返回工作流任务，不再返回 `type=agent`。验证：`tests/dashboard` 的活动用例断言窗口内没有智能体更新，分页参数行为不变。

## 2. 前端平台概览

- [x] 2.1 删除「活跃智能体」，按顺序渲染在线设备、平台助手、工作流、运行中任务、任务数量；运行中副标题固定「排队 N」，两张助手卡进入 `/ai-assistant`，两张任务卡进入 `/tasks`。验证：`cd frontend && npx vitest run tests/dashboard` 断言卡序、文案与路径。
- [x] 2.2 仅运营渲染「运营配置」子区及三张卡，数值取 `ops`，分别进入 `/ops/users`、`/ops/agents`、`/ops/model-configs`；普通用户不渲染该子区。验证：dashboard 前端测试分别用运营与普通用户响应断言子区有无。
- [x] 2.3 结果行点击进入 `/tasks`，中断与取消使用各自文案，不再显示「未执行」。验证：`TaskResultPanel` 测试断言路由与两档文案。

## 3. 关单

- [x] 3.1 跑后端门禁与边界检查。验证：`python manage.py check`、`ruff check backend/apps/dashboard`、`python -m pytest -c tests/pytest.ini tests/dashboard -q`、`python utils/gen_arch_stats.py --check-boundaries` 均通过。
- [x] 3.2 跑前端类型与样式门禁。验证：`cd frontend && npx vue-tsc --noEmit` 与 `npm run lint:styles` 通过。
- [x] 3.3 目视验收：运营看到七张运行/运营卡加用例卡，普通用户看不到运营配置；排队为 0 仍显示「排队 0」。验证：两种身份各打开一次仪表盘并记录结果。
