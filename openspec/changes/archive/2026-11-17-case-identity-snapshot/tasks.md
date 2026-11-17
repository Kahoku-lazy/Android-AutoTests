## 1. 用例身份落库

- [x] 1.1 `Task` 新增 `case_identity` JSON 字段，默认 `{}`；生成迁移。验证：`python manage.py makemigrations --check` 无待生成迁移，`python manage.py check` 通过。
- [x] 1.2 在 `task_list` 增加无 Django 依赖的 `case_identity_label`：空身份返回空串，里程碑返回「里程碑」，一条返回标题，多条返回「第一条 · 共 N 条」，空标题写成「未命名用例」。验证：`python -m pytest -c tests/pytest.ini tests/task/unit -k case_identity -q` 通过。
- [x] 1.3 `case_manager.api` 增加只读函数，按 `case_ids` 顺序返回 `{project,id,title}`；不存在、无权限、功能用例的拒绝原因与现有编译一致。验证：`python -m pytest -c tests/pytest.ini tests/task/api/test_task_submit_sop.py -q` 覆盖拒绝路径并通过。
- [x] 1.4 平台提交在同一事务内创建任务、写入平台身份、保存附件；上传里程碑写入 `{"source":"milestone","rows":[]}`。任务标题仍是工作流名。验证：上述提交测试断言两条平台用例的顺序、项目名与当时标题，以及上传任务不把文件名写入身份。
- [x] 1.5 `rerun_task` 原样复制 `case_identity`，不回读用例库。验证：重跑测试断言新任务身份与原任务一致，原用例改名后仍不变。

## 2. 任务清单展示

- [x] 2.1 任务列表序列化下发 `case_label` 与 `case_rows`，不回读用例库，不改 `title`。验证：`python -m pytest -c tests/pytest.ini tests/task/api -k "list and case_identity" -q` 通过。
- [x] 2.2 任务清单在工作流列后增加「用例」列：空值显示「—」，非空显示 `case_label`；多于一条时悬停按顺序显示「项目 / 标题」。验证：`cd frontend && npx vitest run tests/task-list` 通过。

## 3. BUG 单抄录

- [x] 3.1 `BugTicket` 新增 `case_label` 与 `case_rows`，默认空，不回填。验证：`python manage.py makemigrations --check` 与 `python manage.py check` 通过。
- [x] 3.2 登记时只读 `Task.case_identity` 并抄录文案与行列表；标题和 `source_ref` 不变。重复登记不覆盖处理状态，也不用空身份擦掉已抄录文案。验证：`python -m pytest -c tests/pytest.ini tests/bug_ticket/unit -q` 通过。
- [x] 3.3 列表与详情下发用例身份；关键字增加 `case_label`。详情在元信息展示用例，多于一条时列出「项目 / 标题」；空身份不渲染该行。验证：`python -m pytest -c tests/pytest.ini tests/bug_ticket/api -q` 与 `cd frontend && npx vitest run tests/bug-manager` 通过。

## 4. 仪表盘副行

- [x] 4.1 `recent_tasks` 增加 `case_label`，活动时间线不改。前端只在非空时渲染副行。验证：`python -m pytest -c tests/pytest.ini tests/dashboard -q` 与 `cd frontend && npx vitest run tests/dashboard` 通过。

## 5. 关单

- [x] 5.1 跑边界与风格检查：`python utils/gen_arch_stats.py --check-boundaries`，以及本次改动路径的 `ruff check`。验证：两条命令退出码为 0。
- [x] 5.2 人工核对一条平台多选任务：任务清单、BUG 详情、仪表盘三处文案相同，任务标题与 BUG 标题未被用例名替换。验证：三处截图或接口响应一致。
