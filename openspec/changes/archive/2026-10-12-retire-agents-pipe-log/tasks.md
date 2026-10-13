## 1. 去掉管道日志模块

- [x] 1.1 删除 `engines/agents/process_log.py` 与 `engines/agents/messaging/events.py`。`messaging/__init__.py` 不再导出 `EventStreamRecorder`。`messages.py` 保留。验证：`rg -n "AgentProcessLog|EventStreamRecorder|process_log" engines/agents` 无匹配；`python -m ruff check engines/agents/messaging/__init__.py` 无新增问题

## 2. 角色与 SOP 只留对话稿

- [x] 2.1 `BaseRole` 去掉过程日志字段、`start` 的 `log_enabled` / `log_path`，以及单轮回复上的记录器。`独立运行` 改为角色模块内常量。命令行入口不再打开 `logs/sop.log`，也不再把过程日志传给 runner。验证：`rg -n "log_enabled|log_path|process_log" engines/agents/role` 无匹配；`python -m ruff check engines/agents/role/base.py engines/agents/role/sop.py` 无新增问题
- [x] 2.2 `SopRunner` 去掉 `log` 参数、管道记录器与管道用量汇总。启动输入、步骤开始、事件与费用、结束汇总仍只写对话稿。验证：`rg -n "DialogueLog|write_summary" engines/agents/role/sop.py` 能看到对话稿接入，且同文件没有 `self.log.write`；`pytest tests/graybox/unit/test_sop_log_empty_abort.py tests/graybox/unit/test_agent_dialogue_log.py -q` 通过

## 3. 确认边界

- [x] 3.1 确认平台过程日志未动，演示页未改成运行产物。验证：`rg -n "class AgentProcessLog" engines/ai/process_log.py` 仍有该类；`rg -n "dialogue-log-demo|html" engines/agents/role/sop.py engines/agents/messaging/dialogue.py` 无 HTML 生成
