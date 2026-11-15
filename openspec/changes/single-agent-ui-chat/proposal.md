## Why

平台小助手现在是「角色卡 + 模型池」，对话直接打模型，不经过智能体，也看不到一次回复里的工具与事件。需要一条只有一个智能体的编排：左边选编排，右边对话，事件由中间件观察。SOP 多角色流程本期不动。

## What Changes

- 新增单智能体编排目录。第一张卡片是「Android UI 控制」，复用现有 UI 执行角色，不新建第二套工具或提示词。
- 新增单智能体事件中间件：只观察这一个智能体的 `on_reply`，把事件折进现有接收方。SOP 角色不挂它。
- **BREAKING** 平台小助手入口改为两栏：左边编排卡片，右边对话框。原角色卡与模型池不再占这一页。
- 对话前必须选择当前设备。未选设备时可以看卡片，不能发送会操作设备的消息。
- 模型直连对话页保留路由，但不作为本页入口。

## 关联文档

无关联 PRD。原因：这是把已有 UI 执行角色接到助手对话页，不改变设备任务与用例编写的验收口径。

## Capabilities

### New Capabilities

- `single-agent-workflow`: 单智能体编排的目录、卡片清单，以及「Android UI 控制」只跑一个执行角色。
- `single-agent-chat`: 助手页选择编排卡片后，经该智能体对话；事件由中间件观察；操作前必须有当前设备。

### Modified Capabilities

- `ai-assistant/assistant-board-layout`: 入口从角色卡改为编排卡片加对话框；卡片仍直接放在页面背景上。

## Impact

- 引擎：`engines/agents/workflow/single/`、`engines/agents/middleware/`。不改 `ui_auto_workflow.py` 与 SOP 事件消费。
- 后端：`backend/apps/ai_assistant` 增加编排清单与单智能体对话接口。engines 不写库。
- 前端：`frontend/src/modules/ai-assistant/index.vue` 换成左卡片、右对话；设备选择复用设备池的当前设备。
- 测试：编排只建一个 Agent；中间件能看到该 Agent 的回复事件；未选设备时发送被拒绝。
