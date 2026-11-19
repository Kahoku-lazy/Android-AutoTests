## Why

工作流现在把「执行者加验收者」的编排，和「设备加里程碑」的 UI 自动化种类焊在一起。换两张名片做用例编写或需求拆解，保存得了，启动后仍按手机 UI 跑。

## What Changes

- 工作流拆成两条轴：编排（`sop` / `goal` / `team`）与种类（`ui_automation` / `case_authoring` / `requirement_breakdown`）。一次运行是一种编排加一种种类。
- 只允许三对：`sop + ui_automation`、`goal + case_authoring`、`team + requirement_breakdown`。其它组合创建时拒绝。
- **BREAKING**：工作流绑定不再固定为执行者与验收者两列。SOP 与 Goal 仍是这一对；Team 是一个队长加多名成员，没有验收者。
- 任务在启动时冻结工作流编号、编排与种类。之后修改工作流不影响已创建的任务。
- UI 自动化保持现有行为：必须选设备，按设备排队，输入是平台用例或里程碑 YAML。
- 用例编写按一个模块的材料整份编写并验收，不占设备，产物进入用例库。
- 需求拆解只产出模块边界、测试点与不覆盖范围，不写具体用例，不操作设备，也不自动创建后续任务。
- 三段之间人工交接：拆解结果确认后，再为其中一个模块启动用例编写；用例入库后，再由现有 SOP 从平台选用例。
- 报告与 BUG 按冻结的种类区分。需求拆解新增 BUG 分类「需求拆解」。

## 关联文档

无独立需求编号。本次范围来自本轮确认：通用编排暂定 SOP、GoalPipeline、TeamPipeline；Goal 配用例编写，Team 配大需求拆解且只交边界与测试点；需求拆解 BUG 使用新分类。`PRD-平台总需求.md` 仍把工作流描述成单一的执行加验收流程，本变更会补上编排与种类。

## Capabilities

### New Capabilities

- `workflow-orchestration-kinds`：工作流按编排与种类组合，三对组合各自规定绑定、输入、产物和拒绝条件。

### Modified Capabilities

- `assistant-bound-sop`：工作流记录从固定两张名片改为按编排保存绑定；运行弹窗按种类切换输入。
- `ai-task-list`：任务行展示冻结的编排与种类，附件列按种类解释。
- `ai-task-publishing`：重新执行沿用冻结的编排、种类与工作流编号，并覆盖成功、失败、取消、中断。
- `bug-ticket-management`：新增需求拆解分类，并按任务冻结的种类归类。
- `report-ai-task-list`：报告清单按种类显示来源，拆解报告不要求设备或用例名。

## Impact

- 后端：`backend/apps/ai_assistant/` 的工作流模型与接口，`backend/apps/task_list/` 的提交、重跑与调度，`backend/apps/bug_manager/` 的分类，`backend/apps/report_generator/` 的报告行。
- 引擎：`engines/backend_bridge/workflow/` 增加 Goal 与 Team 的薄适配，不重写官方循环。
- 前端：`frontend/src/modules/ai-assistant/` 的工作流卡片、配置弹窗与任务弹窗，`frontend/src/modules/task-list/` 的状态与操作。
- 测试：工作流组合校验、三类任务启动、重跑冻结字段、BUG 分类与报告行。
