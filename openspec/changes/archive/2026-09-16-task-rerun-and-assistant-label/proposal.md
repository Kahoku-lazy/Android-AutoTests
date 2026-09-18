## Why

失败任务卡片只能看详情，无法用同一套标题/目标/设备/附件再跑一遍；若覆盖原记录会丢失失败现场。同时卡片没有执行该任务的助手名称（线路卡上的「UI 视觉自动化」），改名后历史卡片也无法对齐。

## What Changes

- 失败任务卡片增加「重新执行」：读取原任务信息，**新建**一条 pending 任务并进入现有调度，原任务保留不动。
- 任务卡片增加「助手」展示，文案为当前平台小助手线路名称（与看板 `route-agent-name` 一致，如「UI 视觉自动化」）。
- 线路/智能体名称变更后，列表与详情中的助手名 MUST 立即反映新名称，不区分任务是否已执行、已完成或失败。

## 关联文档

- ARCH：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（ai_assistant 任务发布）
- PRD：无独立条目；需求来自工作台验收（失败卡重跑、卡片展示助手名并随改名同步）
- 规格：修改 `ai-task-publishing`（列表卡片字段与提交）

## Capabilities

### New Capabilities

- （无）

### Modified Capabilities

- `ai-task-publishing`: 列表卡片增加助手名（实时取当前线路名）；失败任务可克隆新建并重跑

## Impact

- 后端：`apps/ai_assistant/api.py`（clone/create、列表序列化 `assistant_name`）、`views_drf.py` / `urls.py` 新增重跑端点
- 前端：`TaskBoard.vue` 按钮与助手行、`useTaskList` / `api/tasks.ts`、`shared/types/ai.ts`
- 写库仍走 `api.py`；调度复用 `dispatch_device`
- 测试：clone 不覆盖原任务；列表助手名随 route name 变化
