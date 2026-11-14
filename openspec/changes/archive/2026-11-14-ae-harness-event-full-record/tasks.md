## 1. 开关与公共字段

- [x] 1.1 `event/record.py` 的记录器增加仅关键字入参 `full`（默认 `True`），并在说明里写清「全量 = 字段全 + 不截断 + 仍折叠」。验证：`python -c "import inspect; from engines.ae_harness.event.record import AgentEventRecorder; print(inspect.signature(AgentEventRecorder.__init__))"` 中 `full` 默认值为 `True`
- [x] 1.2 事件行统一补 `created_at` 与 `event_id`（取不到则不写该字段）。验证：单测用带这两个属性的替身事件断言字段存在；不带时不出现
- [x] 1.3 `metadata` 非空时记录，并做 JSON 化兜底。验证：单测传非空 metadata 断言写入；传不可序列化对象不抛错

## 2. 作用域字段与文本块

- [x] 2.1 `ReplyStartEvent` / `ReplyEndEvent` 行补 `session_id`。验证：单测断言两行都含会话标识
- [x] 2.2 `HintBlockEvent` 行补 `source`。验证：单测断言 `hint` 与 `source` 同时存在
- [x] 2.3 `TextBlockEndEvent` 行补 `text`（全量模式）。验证：单测断言该字段为该块最终文本

## 3. 取消截断（仅全量模式）

- [x] 3.1 思考块正文全量模式下不截断；`full=False` 仍按 600 截断。验证：单测用长思考文本分别断言长度
- [x] 3.2 工具结果输出全量模式下不截断；`full=False` 仍按 4000 截断。验证：单测用长输出分别断言长度

## 4. 折叠与边界

- [x] 4.1 增量事件仍不逐条落盘：全量模式下产物中不出现 `*DeltaEvent` 行。验证：单测喂 100 条思考增量，断言只出现块结束行
- [x] 4.2 观测行不受开关影响。验证：单测在两种模式下比较观测行字段集合相同
- [x] 4.3 `event/AGENTS.md` 登记全量模式与字段口径。验证：人工核对文档与代码一致

## 6. 关联键（补齐信息损失）

- [x] 6.1 工具调用行与工具结果行写入同一个工具调用标识。验证：单测断言两行标识相同且能据此配对
- [x] 6.2 思考块行与文本块行写入框架侧的块标识。验证：单测断言两行各带 `block_id` 且互不相同
- [x] 6.3 关联键与全量开关无关，始终写入。验证：非全量模式下单测仍断言标识存在
- [x] 6.4 真机冒烟：同一 `tool_call_id` 在调用行与结果行同时出现。验证：读 JSONL 抽查

## 7. 测试与门禁

- [x] 7.1 `tests/engines/ae_harness/unit/test_record_usage.py` 增补开／关两组用例。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness -q` 全绿
- [x] 7.2 `python -m scripts.docstrings check --path engines/ae_harness` 归零。验证：0 error / 0 warn
- [x] 7.3 `ruff check` 与 `ruff format --check`（engines/ae_harness + tests/engines/ae_harness）全过。验证：退出码 0
- [x] 7.4 `python run.py check` 与基线对比无新增失败项。验证：失败项集合与基线一致
- [x] 7.5 真机冒烟一次，确认产物含 `created_at` / `session_id` / `source` 且思考未截断。验证：读 JSONL 抽查字段
