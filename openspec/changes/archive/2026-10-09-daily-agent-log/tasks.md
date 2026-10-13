## 1. 引擎：按天切分

- [x] 1.1 `AgentProcessLog` 改为「基路径 + 当天日期」派生当日文件（形如 `agents-20261009.log`），每次写入前解析目标文件并追加；验证：单测断言当日文件名、目录自动创建、既有内容不被覆盖
- [x] 1.2 跨天自动切换：把"当天日期"抽成可替换函数，单测用 monkeypatch 固定两天，断言零点后的记录进新文件、旧文件内容不变；验证：`pytest tests/graybox/unit/test_agent_process_log.py -q` 全绿
- [x] 1.3 首次创建与跨天切换时向应用日志（python logging）记一条 info，说明当前文件路径；验证：单测用 caplog 断言该 info 出现
- [x] 1.4 确认不自动删除历史文件；验证：单测放一个"前一天"的文件，写入后断言其内容与存在性不变

## 2. 平台与文档口径

- [x] 2.1 `engine_adapter.agent_log_path()` 注释与口径同步为"注入基路径，按天派生"；验证：`python manage.py check` + `ruff check apps/ai_assistant` 通过
- [x] 2.2 过程日志模块与相关文档里的落点说明同步（不再写"单文件 agents.log"）；验证：全仓 grep `agents.log` 命中的说明文字口径一致

## 3. 回归与归档

- [x] 3.1 过程日志与工作流相关单测全绿；验证：`pytest tests/graybox/unit -q -k "agent_process or workflow or executor_log"` 
- [x] 3.2 门禁：`python manage.py check`、`ruff check` + `ruff format --check`（相关路径）、`python tools/gen_arch_stats.py --check-boundaries` 通过
- [x] 3.3 真机跑一步，确认生成当日文件且实时追加；验证：留存文件路径与片段
- [x] 3.4 归档：`openspec validate --strict` 通过，delta 同步进主规格
