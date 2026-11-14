# workflow/single AGENTS.md

> 层级：根 `AGENTS.md` → `engines/AGENTS.md` → `engines/agents/AGENTS.md` → **本文件**。

本目录只编排**一个智能体**。不创建第二个角色，不调用 SOP 引擎。

| 文件 | 职责 |
| --- | --- |
| `catalog.py` | 卡片清单（**当前为空**：平台对话角色已迁到 `engines/backend_bridge`）。页面与接口只读这里 |
| `android_ui.py` | Android UI 控制：复用 `build_ui_executor()`，挂事件中间件 |
| `__init__.py` | `session_for`：同一连接复用一个实例 |

红线：MUST NOT import `AgentSOPWorkflow` / `ui_auto_workflow`。工具不在这里绑定。
