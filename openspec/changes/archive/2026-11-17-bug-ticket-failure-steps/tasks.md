## 1. 收口留下失败步骤

- [x] 1.1 `task_runner.py` 在成功收口载荷写入 `failed_steps`：序号、步骤名、期望结果、实际结果、尝试次数、`kind`。期望结果按步骤 YAML 同序配上，取不到写「未记录」。验证：`python -m pytest -c tests/pytest.ini tests/task/unit/test_task_closeout.py -q` 断言一步没通过时四问齐全，且 `workflow_id` 仍在。
- [x] 1.2 抛错路径与清扫中断路径写入同形的一步。内存里已有没通过的步骤时保留这些步骤，不被 `provider` / `device` / `platform` 短路丢掉。验证：同一测试文件覆盖模型拒绝、无步骤结论、`process_lost`，且列表摘要仍是短句。

## 2. BUG 单保存快照

- [x] 2.1 `BugTicket` 增加可空 JSON 字段 `failure`，迁移可逆。验证：`python manage.py makemigrations --check` 无残留，`python manage.py check` 退出码为 0。
- [x] 2.2 `extract.py` 对带 `failed_steps` 的 `assistant_sop` 只出一张，来源键 `task`，标题用第一个失败步骤；没有快照的旧任务仍按用例拆。写库仍只经 `bug_manager.api`。验证：`python -m pytest -c tests/pytest.ini tests/bug_ticket/unit/test_bug_ticket_extract.py tests/bug_ticket/unit/test_bug_ticket_api.py -q`。
- [x] 2.3 列表与详情返回 `failure_steps`；详情仅在任务仍在且结果含报告定位时返回 `report_run` / `report_name`。验证：`python -m pytest -c tests/pytest.ini tests/bug_ticket/api/test_bug_tickets.py -q`。

## 3. 详情按四问展示

- [x] 3.1 详情抽屉有快照时按出错步骤、原因类别、期望结果、实际结果展示；第一项展开，其余折叠。无快照时沿用现有错误卡。字号只取 16px / 14px，不新造卡片皮肤。验证：`cd frontend && npx vitest run tests/bug-manager`。
- [x] 3.2 有报告定位时提供「查看报告」，复用任务清单已有的报告读取；没有时只显示任务编号。列表关联任务列去掉 `/tasks/:id` 链接。验证：同一前端测试断言死链不存在，且 `cd frontend && npm run lint:styles` 退出码为 0。

## 4. 门禁

- [x] 4.1 后端边界与相关测试：`python -m pytest -c tests/pytest.ini tests/task/unit/test_task_closeout.py tests/bug_ticket -q`，以及 `python utils/gen_arch_stats.py --check-boundaries`。验证：两条命令退出码为 0。
- [x] 4.2 `openspec validate --change bug-ticket-failure-steps`。验证：命令退出码为 0。
