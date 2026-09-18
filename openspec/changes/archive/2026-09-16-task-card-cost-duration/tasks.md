## 1. 列表契约

- [x] 1.1 在 `serialize_agent_task_row` 增加 `deepseek_cost`、`started_at`、`finished_at`，扩展 `test_serialize_row_includes_device_label`（或同文件新测）断言费用数字与时间字符串；`pytest tests/graybox/unit/test_ai_task_title_attach_dispatch.py` 通过

## 2. 卡片展示

- [x] 2.1 `TaskRecord` 增加上述字段；`TaskBoard` meta 增加费用（四位小数 + 元）与耗时（复用 `formatTaskDuration`）
- [x] 2.2 补前端断言或现有 task list 相关 spec 覆盖新字段展示口径

## 3. 门禁

- [x] 3.1 相关 pytest 与前端类型检查范围内通过
