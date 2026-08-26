# ai_assistant App AGENTS.md

> 全局边界 / 协议要点 / 关单清单 → `../AGENTS.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v1.0 · 最后更新：2026-08-21 · v1.0：从已归档 `dev_docs/_archive/后端claude笔记.md` §0️⃣ 模块表迁出并展开。

## 红线（全局索引表 ai_assistant 行的展开）

| 只做 | 禁止 |
|------|------|
| 对话（唯一 SSE 流）、Agent/Toolbox/知识库 CRUD、上传 | 直接调模型以外的业务写库（写库走各模块 api） |
| Tool 只调各模块 `api.py`（同进程直调） | import 其他 App 的 service/runner/内部实现 |

- **Tool 写库只经目标模块 api.py**——幻觉写库、绕过防火墙是本 App 头号红线；新增 Tool 必须走 `api.py` + `--check-boundaries` 验证。
- AgentScope 同进程运行、依赖 Redis：Redis 不可用 → 前端降级阻塞模式 `POST /api/ai/chat/sync`（双边已约定，勿删降级路径）。
- SSE 事件类型是双边契约（前端 §3 事件表），变更必须同步前端 `AGENTS.md` §3 + 本文。

## 本 App 契约（特例 + 真相源）

真相源：`apps/ai_assistant/urls.py`（router 无尾斜杠：`agents` / `conversations` / `toolbox` + special：`agents/health` / `models/detect` / `available-tools` / `available-skills` / `tasks` / `knowledge/*` / `upload-*` + **豁免 legacy**：SSE `conversations/{id}/chat/stream` + 工具网关 `tools/schemas` / `tools/agent-config/{id}` / `tools/{module}/{action}`）。

- **router `trailing_slash=False`**：保持旧路径无尾斜杠匹配——新增路由必须延续无尾斜杠约定，否则旧前端 404。
- SSE 与工具网关两条 legacy 路径是「豁免不迁移」：改签名必须同步前端 + Tool 注册表。
- 工具网关 `tools/{module}/{action}` 经中间件白名单动态分发，新增 action 必须同时更新白名单与 Tool schema。

## 本 App 协议要点

**页面语义增强工具（工具入参 + handler 校验）**：`analyze_page`（inspector/analyze，read_only）纯规则分区，无 LLM；`save_page_semantic`（inspector/save_semantic，write）接收 Agent 在 ReAct 里自然产生的语义命名作为工具入参，handler 经 `llm_semantic.validate_semantic` 校验防幻觉（rid 必须在快照元素集合内）。对齐 `save_case` 的「工具入参 + handler 校验」模式，不依赖 `generate_structured_output`（强制 tool_choice，thinking 模型不支持）。

**SSE（全项目唯一 SSE）**：`/api/ai/conversations/{id}/chat/stream`

- 事件真相源：前端 `AGENTS.md` §3 事件表（`REPLY_START` / `TEXT_BLOCK_DELTA` / `THINKING_*` / `TOOL_CALL_*` / `TOOL_RESULT_*` / `HINT_BLOCK` / `REQUIRE_USER_CONFIRM` / `REPLY_END` / `error`）；新增/改事件必须双边同步。
- 停止生成 = 关闭 SSE 保留已生成内容；`reply_end` 与 `exceed_max_iters` 均为终端事件——未到终端断流前端会报错。

## 关单附加项（全局清单的 delta）

```
[ ] 新 Tool：参数校验/权限 + 只走各模块 api.py（--check-boundaries 通过）
[ ] SSE 事件变更已同步前端 §3 事件表
[ ] 无尾斜杠路由约定未破坏（旧路径 curl 验证）
[ ] 降级路径 POST /api/ai/chat/sync 仍可用（Redis 关闭时）
```
