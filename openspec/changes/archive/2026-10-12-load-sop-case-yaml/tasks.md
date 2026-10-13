## 1. 拆开两边的步骤提示

- [x] 1.1 在 `engines/agents/workflow/steps.py` 的 `_CheckedStep` 上覆盖执行提问与验收提问：执行侧正文只含 `subject`，并保留框架的驳回重试说明；验收侧正文只含 `description`，交接内容与挂起恢复保持框架原样。验证：`python -m pytest tests/graybox/unit/test_sop_steps.py -q` 中「两边各看各的」用例通过，且原有装配用例仍通过。
- [x] 1.2 在 `tests/graybox/unit/test_sop_steps.py` 增加不调用模型的用例：动作为「点击开关」、结果为「日志出现关闭成功」时，执行提示含动作且不含结果，验收提示含结果且不含动作；已有一条驳回时，驳回说明只出现在执行提示。验证：同上 pytest 命令通过。

## 2. 手工入口读取 YAML

- [x] 2.1 在 `engines/agents/agents.py` 增加 `load_sop_cases(path)`：`yaml.safe_load` 读取单个映射或非空列表中的每条用例，`title` 作流程名，`action` / `assert` 按顺序变成 `SopStepInput`；路径缺失、文件不存在、列表为空、缺字段或空白时在装配前失败。每条用例单独 `start()` 后跑一遍，`max_attempts` 保持 2，设备 ID 开场输入不改。验证：`python -m pytest tests/graybox/unit/test_sop_case_yaml.py -q` 通过。
- [x] 2.2 新增 `tests/graybox/unit/test_sop_case_yaml.py`：用临时 YAML 覆盖单条列表、单个映射、两步顺序、两条用例按顺序装配、缺 `assert`、文件不存在。验证：该文件 pytest 通过；`python -m ruff check engines/agents/agents.py engines/agents/workflow/steps.py tests/graybox/unit/test_sop_steps.py tests/graybox/unit/test_sop_case_yaml.py` 通过。不跑全量回归，不改 `SopRunner` / `SOPEngine`。

## 3. 按用例汇总

- [x] 3.1 `final_summary` 按标题逐条输出 PASS 或 FAIL；FAIL 下列出失败步的步序、动作和驳回说明，未开始的后续步骤不列入。末尾输出总耗时和合计 token、费用。验证：`python -m pytest tests/graybox/unit/test_sop_case_yaml.py -q` 中汇总用例通过。
