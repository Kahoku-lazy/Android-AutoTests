## Why

SOP 运行已经写成任务，但侧栏「AI任务」进不去任务清单，提交成功后也只有一个编号。用户要自己找页面，找到后 SOP 任务还被标成设备执行。

## What Changes

- 侧栏「AI任务」补回「任务清单」，指向已有 `/tasks`。不新建页面，不新建任务表。
- 任务卡按 `task_kind` 显示三类：设备执行、用例编写、SOP。`assistant_sop` 不再显示成设备执行。
- 助手页工作流任务提交成功后仍留在本页，提示里增加可点的「去任务清单」。不自动跳转。
- `POST /api/tasks/submit/`、弹窗字段、工作流卡片都不改。

## 关联文档

无独立需求编号。动机来自已审方案：SOP 任务复用已有任务清单，侧栏文案用「任务清单」，成功后只给链接。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ai-task-list`: 任务卡类型按 `task_kind` 区分 SOP；工作流提交成功后给出进入任务清单的链接，且不离开当前页。
- `frontend-sidebar-nav`: 「AI任务」分组补回「任务清单」入口，路径为 `/tasks`。

## Impact

- 前端：`sidebarNavConfig.ts`、`task-list` 任务卡类型文案、`ai-assistant` 提交成功提示。
- 后端与提交接口不变。
- 测试：侧栏顺序、任务卡三类文案、成功提示含链接且不跳转。
