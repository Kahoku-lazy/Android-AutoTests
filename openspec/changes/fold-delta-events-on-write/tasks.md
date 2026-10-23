## 1. 模型与写库

- [x] 1.1 `models.py`：`TaskEvent` 加 `delta_count`（PositiveIntegerField，默认 1）；生成迁移。验证：`makemigrations --check` 与测试库迁移通过。**验证结果**：`0003_taskevent_delta_count` 已应用；`makemigrations --check` 输出 No changes detected。
- [x] 1.2 `event_store.py`：`TaskEventSink` 增加未结束增量行；同类型/步骤/尝试累加 `delta_count` 与整段耗时；类型或步骤变化、`close()` 时落行；`seq` 在落行时分配；批量 flush 不切断未结束行。验证：单测覆盖 3 片段→1 行、跨 flush 不拆、换步骤拆两行、`close` 收尾。**验证结果**：`test_consecutive_deltas_fold_into_one_row` / `test_delta_run_survives_batch_flush`（120 条仍 1 行）/ `test_step_change_splits_delta_run` 全过。

## 2. 报告读取

- [x] 2.1 `task_reports.py`：`_SLIM_COLUMNS` / `_EventRow` 读取 `delta_count`；`_grouped` 用段内 `delta_count` 之和作为 `count`；旧数据默认 1 行为不变。验证：`test_task_event_flow.py` 全绿，折叠行与逐条增量两种数据都显示正确 `×N`。**验证结果**：9 passed；任务 141 报告字节数与折叠前完全一致（10,475,452 B）。
- [x] 2.2 新增用例：直接构造一条 `delta_count=17447` 的增量行，报告该项 `count` 为 17447、时间取该行时刻；再构造 3 条 `delta_count=1` 的旧式增量，`count` 仍为 3。验证：pytest 通过。**验证结果**：`test_folded_delta_count_is_used_directly` 通过；旧式 3 条增量的既有用例仍为 count=3。

## 3. 验证

- [x] 3.1 行数与体量：对任务 141/142 统计折叠后应有的行数；迁移后事件表体积对比。验证：脚本输出。**验证结果**：141 **147,850 → 9,602 行（-93.5%）**；142 **174,098 → 8,640 行（-95.0%）**；按此比例全表 651,834 行预计降到约 4.5 万行、152 MB 降到约 15 MB（历史数据未回溯，实际占用待新任务积累后体现）。
- [x] 3.2 静态与规格门禁：`ruff check` / `ruff format --check` / `openspec validate fold-delta-events-on-write --strict`。验证：退出码 0。**验证结果**：ruff 全过；openspec valid。
