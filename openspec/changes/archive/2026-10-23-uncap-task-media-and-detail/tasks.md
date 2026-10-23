## 1. 取消截图上限

- [x] 1.1 `backend/apps/task_list/api.py`：删除 `TASK_MEDIA_LIMIT` 常量与 `store_task_media` 的计数分支，保留按任务内 `sha256` 去重与“只存缩略图”行为；docstring 同步。验证：`python -m pytest -c tests/pytest.ini tests/api/test_task_event_store.py -q` 全绿。**验证结果**：5 passed。
- [x] 1.2 `tests/api/test_task_event_store.py`：把“超过上限不再新增”改成“超过 300 张仍新增”，用 `bulk_create` 预置 300 行后断言第 301 张返回编号；保留删除任务级联用例。验证：该文件用例全绿。**验证结果**：`test_media_has_no_count_cap_and_cascade_delete` 通过（301 行，级联删除后 0 行）。

## 2. 明细完整展示

- [x] 2.1 `backend/apps/task_list/task_reports.py`：新增 `_text()`（去回车、去首尾空白、不截断），`_detail` 的七处 `_clip` 改为 `_text`；`_clip` 改为只给 `data.task.result` 用的 `_result_summary`（240 字）。验证：`python -m pytest -c tests/pytest.ini tests/api/test_task_event_flow.py -q` 全绿。**验证结果**：8 passed。
- [x] 2.2 新增用例：文本块 3,000 字与工具入参约 2,800 字时 `detail` 与原文一致、不以省略号结尾；`task.result` 仍为 240 字摘要。验证：`tests/api/test_task_event_flow.py` 新增用例通过。**验证结果**：`test_detail_keeps_full_text_and_task_result_stays_short` 通过。
- [x] 2.3 `openspec/specs/task-media-delivery/spec.md` 的 Purpose 去掉“采集上限”表述，改为“按内容去重、不设张数上限”。验证：文案与 `tests/api/test_task_event_store.py` 行为一致。**验证结果**：Purpose 已更新。

## 3. 门禁与规格

- [x] 3.1 静态检查：`ruff check` 与 `ruff format --check` 覆盖改动文件。验证：退出码 0。**验证结果**：4 files already formatted；All checks passed。
- [x] 3.2 复测影响：对任务 142 运行报告，确认 `media_id` 覆盖全部截图事件（历史缺失除外），记录 `detail` 变长后的响应体积与聚合耗时。验证：脚本输出。**验证结果**：任务 142 的 seq 173974 明细由 241 字变为 2,858 字（完整 JSON，无省略号）；任务 141 报告 8.69 MB → 10.48 MB（+20.5%），聚合 2.22–3.02 s（与改动前同一量级）；`task.result` 仍 241 字。
- [x] 3.3 规格校验：`openspec validate uncap-task-media-and-detail --strict` 通过。验证：命令输出通过。**验证结果**：valid。
