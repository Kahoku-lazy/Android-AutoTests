## Context

见 proposal.md - Why。与方案直接相关的现状：

- UI 执行角色已由 `build_ui_executor()` 转调 `assistant.create_agent`，工具模块是 `device` + `observe`。
- 设备任务走 `workflow/ui_auto_workflow.py` 的双角色 SOP。用户要求这期不动。
- 助手页是左角色卡、右模型池。模型对话走 `POST /api/ai/chat/stream/`，不经过智能体。
- 设备池已有当前设备选择，助手页不另建数据源。
- AgentScope 2.0.9 的 `on_reply` 只包住一个智能体的一次回复。单智能体没有 SOP 引擎转发事件，所以事件观察放在中间件。

## Goals / Non-Goals

**Goals:**

- `workflow/single/` 只编排一个智能体。第一张是 Android UI 控制。
- 事件中间件只挂在这条单智能体上，复用现有 `AgentEventsShow` 写接收方。
- 助手入口改成左卡片、右对话；发送前必须有当前设备。

**Non-Goals:**

- 不改 SOP、不新增 SOP 事件消费器。
- 不把知识库文字会话和 Omni 语音迁到这套编排。
- 不在助手页重做模型池。模型直连路由保留，只是不再占入口。
- 不做人工工具确认。设备工具仍按现有自动放行。

## Decisions

### 1. 目录 `engines/agents/workflow/single/`

只放单智能体编排。`android_ui.py` 提供清单项和 `run(serial, message)`。内部调用 `build_ui_executor()`，把序列号放进当轮用户消息，然后 `reply_stream`。不调用 `AgentSOPWorkflow`。

备选是在 `ui_auto_workflow.py` 加一个单角色模式。否决：该文件的契约是每步一对角色，混进去会让「SOP 先不动」失真。

### 2. 事件中间件只挂给这次创建的实例

新增 `middleware/reply_events.py`，实现 `on_reply`：转发内层事件，同时交给 `AgentEventsShow`。它不注册进默认 `build_agent_middlewares`。`android_ui` 在创建后把这个中间件放进该实例的中间件列表。

SOP 的 `build_ui_executor()` 不传这个中间件。这样同一角色定义，两条运行路径的事件出口不同，不会双写。

备选是改 `build_ui_executor` 默认挂上。否决：SOP 引擎已经转发这些事件，再挂就会落两条。

### 3. 连接内复用一个 Agent

一次对话连接建一个执行者。后续消息调用同一个实例的 `reply_stream`，上下文留在实例里。连接结束即丢弃。这和知识库文字会话的「不跨连接」一致。

设备序列号每条消息都重放。用户中途换设备时，下一条消息带新序列号，不新建智能体。

### 4. 后端只做通道

`ai_assistant` 新增：

- `GET /api/ai/workflows/`：返回单智能体清单。
- `POST /api/ai/workflows/android_ui/stream/`：请求体含 `serial`、`message`、`session_id`。后端按 `session_id` 取或建运行器，流式把文本和事件摘要推给前端。

engines 不 import Django。运行器放在 `workflow/single/`，后端只调用它。

未知 `workflow` 键返回 404。缺 `serial` 返回 400，不创建智能体。

### 5. 前端替换入口两栏

`/ai-assistant/agents` 仍是入口。左栏渲染清单卡片，选中态落在页面状态。右栏是对话框，顶部是当前设备选择，数据来自现有设备列表接口。

未选卡片或未选设备时，发送按钮不可用。选中 Android UI 控制后，发送走新的 workflow 流，不走 `/api/ai/chat/stream/`。

模型对话页 `/ai-assistant/chat/:model` 保留，入口按钮从这页移除。

### 6. 视觉沿用现有助手卡片

左栏卡片复用 `AgentRouteCard` 的尺寸与头像规则，文案改成编排名和「单智能体」。不新做一套卡片皮肤。对话框复用现有聊天气泡与发送条，不引入新颜色。

## 模块防火墙自检

- `workflow/single` 不 import `apps` / `django`，不在 workflow 里绑 `tool_*`。工具仍由 `build_ui_executor` 经 `tools_config` 注入。
- 中间件不 import workflow。它只观察事件。
- 后端不在 View 里创建模型或拼提示词。只调用 `workflow/single` 的公开入口。
- 前端不直连数据库。设备列表走现有设备 API。
- 不新增跨 App 写库。事件仍经现有 `event_sink` 接收方。

## Risks / Trade-offs

- [同一 UI 执行角色两条运行路径] → 事件中间件只由 single 显式挂入；SOP 路径单测继续断言不出现该中间件。
- [对话连接持有设备工具的 Agent] → 连接结束释放；未选设备不创建。不把实例放进进程级全局缓存。
- [入口替换影响原角色配置入口] → 配置页路由保留。左栏卡片对超管仍可进配置，但本期卡片不要求编辑角色。
- [流式事件与浏览器推送重复] → 中间件写接收方；接口流只推给当前对话框。两边内容可以相同，写库只有中间件一处。

## Migration Plan

1. 先落地 `workflow/single` 与中间件，无页面也能单测。
2. 再加后端清单与流式接口。
3. 最后替换助手页。回滚时恢复 `index.vue` 的角色/模型两栏，引擎目录可留着不用。

## Open Questions

无。页面替换与对话前选设备已由用户确认。
