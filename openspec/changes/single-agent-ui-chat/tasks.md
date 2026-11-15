## 1. 单智能体编排

- [x] 1.1 新增 `engines/agents/workflow/single/`，提供编排清单与 `android_ui` 运行入口。验证：清单含 `android_ui` / 「Android UI 控制」；未知键报错。
- [x] 1.2 `android_ui` 只调用 `build_ui_executor()`，把设备序列号放进当轮消息，不调用 SOP。验证：单测断言一次运行只建一个 Agent，且源码不引用 `AgentSOPWorkflow`。
- [x] 1.3 同一 `session_id` 复用一个 Agent，换消息不新建。验证：单测两次 `run` 的 Agent 是同一实例；新 session 是另一个实例。

## 2. 事件中间件

- [x] 2.1 新增 `middleware/reply_events.py`，在 `on_reply` 中把事件交给 `AgentEventsShow`，并继续向外产出事件。验证：假事件经过后接收方收到一条记录，调用方仍能迭代到原事件。
- [x] 2.2 只由 `android_ui` 挂上该中间件，不放进默认装配。验证：`build_ui_executor()` 的中间件列表不含它；`android_ui` 创建出的实例含它。

## 3. 后端通道

- [x] 3.1 `GET /api/ai/workflows/` 返回单智能体清单。验证：接口测试返回 `android_ui`，且路径带尾斜杠。
- [x] 3.2 `POST /api/ai/workflows/android_ui/stream/` 接收 `serial`、`message`、`session_id`。缺序列号返回 400，未知键返回 404。验证：对应接口测试通过，且不创建智能体。

## 4. 助手页

- [x] 4.1 `/ai-assistant/agents` 改为左编排卡片、右对话框。原角色卡与模型池不再出现在该页。验证：页面测试或组件断言左栏有「Android UI 控制」，右栏无模型池。
- [x] 4.2 对话框顶部选择当前设备，数据来自现有设备列表。未选设备或未选卡片时发送不可用。验证：两种空状态下发送按钮禁用，并有「先选择设备」提示。
- [x] 4.3 选中 Android UI 控制后，发送走新的 workflow 流，不走模型直连。验证：请求路径是 `/api/ai/workflows/android_ui/stream/`，请求体含所选序列号。

## 5. 回归

- [x] 5.1 SOP 与模型对话页不被这条路径改坏。验证：`tests/engines/agents/unit/test_workflow_boundary.py` 通过；`/ai-assistant/chat/:model` 路由仍存在。
- [x] 5.2 注释自检。验证：`engines-docstring-check` 对本次新增 engines 文件无新 error。
