## 1. sleep 工具回填

- [x] 1.1 `python manage.py migrate_platform_tools`（dry-run 后执行）——验证智能体 #10 平台工具记录数 = 27，含 `sleep`

## 2. 智能体 04 配置

- [x] 2.1 经 `apps.ai_assistant.api.update_agent` 写入执行 SOP 系统提示词、`max_iters=40`——验证 DB 中 system_prompt/max_iters 生效、`agent_scope_id` 被清空（重建会话生效）
- [x] 2.2 `apps/ai_assistant/agent_scope/tool_registry.py` `get_run_status` 描述补"运行中禁止连续查询，两次查询之间必须用 sleep 等待"——验证 ruff 通过

## 3. 端到端与门禁

- [x] 3.1 真实对话端到端：对话 211 请求"执行 TC-NAV-004"——验证构建日志 `tools=26`、回复完整（无"已达最大推理次数"）、blocks 含 `sleep` 调用（2 次）、最终报告 pass
- [x] 3.2 全部门禁：`manage.py check` + `ruff check apps/ai_assistant` 全绿
- [x] 3.3 `openspec archive tune-agent-execution-flow` 归档本 change
