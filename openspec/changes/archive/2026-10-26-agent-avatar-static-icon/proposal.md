## Why

身份卡头像目前是可配置项：配置页能把本地图片转 data URI 上传，也能填 emoji 或外链。这让同一个助手的身份视觉随手一改就跑偏，上传链路（前端 `FileReader` + `POST /api/ai/upload-avatar/` + 数据库长文本）却只为这一处服务，还带「大图撑大 `ai_agents` 行」的隐患。头像本质是产品身份的一部分，不该由使用者改。

## What Changes

- 头像固定为**内置 SVG 图标**（与用户头像同族的机器人头像），看板卡片与配置页统一使用，不再随数据变化。
- **BREAKING** 配置页下线头像图片能力：删除「上传图片」按钮、隐藏的文件选择器、emoji/外链输入框；「头像」表单项保留只读预览 + 一行「系统内置头像，不可修改」说明。
- **BREAKING** 后端删除 `POST /api/ai/upload-avatar/` 路由与视图；`AIAgent.avatar` 字段与 `route_configs.{route}.avatar` **保留不动**（不做迁移），但前端不再读写。
- 保存智能体的请求体不再携带 `avatar`；看板卡片不再接收头像数据。

## 关联文档

无关联 PRD。本次是界面与接口收敛（下线可配置头像、固定品牌图），来自 2026-10-26 的界面评审，不引入新的需求编号。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ai-assistant/route-card-identity`: 头像改为固定内置图标，不再来自线路配置；「头像边长 = 三行高度」的尺寸约束不变。
- `task-list-module`: 「AI assistant keeps only assistant and route configuration」里「头像上传」不再是 `ai_assistant` 的保留能力。

## Impact

- 前端：新增 `frontend/public/agent-avatar.svg`；改 `modules/ai-assistant/constants.ts`、`index.vue`、`helpers/assistant-cards.ts`、`components/AgentRouteCard.vue`、`components/AgentBasicInfo.vue`、`AgentDetail.vue`、`api/agents.ts`。
- 后端：`apps/ai_assistant/urls.py` 去掉路由；删除 `apps/ai_assistant/views_upload_drf.py`。
- 契约：`openspec/openapi.yaml` 删除 `/api/ai/upload-avatar/`。
- 测试：`frontend/tests/ai-assistant/p0/AgentRouteCard.spec.ts`。
- 不改数据库结构，不需要 migration；历史 `avatar` 值保留在库里但不再参与渲染。
