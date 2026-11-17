## 1. 配置读取收口

- [x] 1.1 在 `config.py` 增加提示词、应用短卡、日志关键词正文的读取函数，并用现有读取测试确认只经该入口打开文件
- [x] 1.2 让 `role_sys_prompts.py` 与 `log_keywords.py` 改为调用这些函数，并用 `tests/config/unit/test_log_keywords.py` 确认缺失文件仍返回空串

## 2. 散文件归位

- [x] 2.1 工具分配留在根上的 `tools_config.py`：`tools/` 强制 `tool_*.py`，分配模块不是工具实现。现有工具分配测试确认导入可用
- [x] 2.2 把 `case_roles.py` 迁入 `assistant/`，根文件只再导出，并用用例角色装配测试确认工具绑定不变
- [x] 2.3 把 `event_log.py` 与 `event_sink.py` 迁入 `messaging/`，根文件只再导出，并用事件落库测试确认接收方协议不变
- [x] 2.4 把 `realtime_vocie_agent.py` 的实现收进 `realtime_vocie/`，根文件只再导出，并用导入检查确认它不直接构造实时语音智能体

## 3. 文档与门禁

- [x] 3.1 更新 `engines/agents/AGENTS.md` 与相关子目录 AGENTS，写明新主人与过渡入口，并确认 `agent_builders.py`、`role_loader.py` 的处理与 design.md 一致
- [x] 3.2 对本次改动运行 docstring 检查与 `python run.py check`，确认没有新增 engines 风格错误

> **2026-11-17 归档**：按需求方决定直接归档，未完成项不再执行；本次 delta 因 MODIFIED 头部缺失未合并，delta 原文保留在本目录 specs/ 下。
