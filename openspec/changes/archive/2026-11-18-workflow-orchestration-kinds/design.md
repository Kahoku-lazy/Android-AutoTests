## Context

见 proposal.md 的 Why。当前 `AISopWorkflow` 只有名称、执行名片、验收名片；工作流编号只写在 `Task.result` 的 JSON 里。`assistant_sop` 任务一律走里程碑 YAML、设备槽和 adb。用例编写已有独立的 `case_authoring` 任务，不读工作流表。BUG 只有 `ui_automation` 与 `case_authoring`。

编排语义以已安装的 AgentScope 2.0.9 为准：SOP 管有序里程碑，GoalPipeline 管一次目标的退回重做，TeamPipeline 管队长向预登记成员分派。三者都是实验接口。

## Goals / Non-Goals

**Goals:**

- 用同一张工作流表表达三种编排，绑定形状由编排决定。
- 任务启动时把组合冻结成自己的列，历史行不再依赖结果 JSON。
- Goal 与 Team 只加调用官方流水线的薄适配。

**Non-Goals:**

- 不实现三对以外的组合。
- 不把 SOP、Goal、Team 自动串成一次运行。
- 不在本变更退役独立的 `case_authoring` 入口。
- 不新增第二种步骤循环、分派循环或报告格式。

## Decisions

### 1. 编排与种类分列，组合用白名单

工作流增加 `orchestration` 与 `kind` 两列。允许的三对放在一处常量，创建、编辑和启动都查它。

备选是只用种类，在种类里隐含编排。这会让以后同一业务换编排时改写历史语义，所以不采用。

### 2. Team 绑定用 JSON，不拆成员表

`sop` 与 `goal` 继续使用现有两列名片编号。`team` 增加 `leader_assistant_id` 与 `members` JSON，每项是 `{assistant_id, description}`。成员数量由规格的「至少两名」约束，不另建表。

备选是统一把所有绑定收成 JSON。现有 UI 工作流已经依赖两列，迁移和回退都会更重，所以不采用。

### 3. 任务冻结为三列

`Task` 增加 `workflow_id`、`orchestration`、`kind`。`workflow_id` 不加外键，删除工作流后历史任务仍可读。新任务创建时写入；`assistant_sop` 旧任务按 `sop + ui_automation` 回填，工作流编号仍可从结果 JSON 回填。重跑读取这三列；旧行没有编号时，才沿同一设备、同一标题、同一用例身份回找。

### 4. 调度按种类分叉

`ui_automation` 继续 `dispatch_device`。`case_authoring` 与 `requirement_breakdown` 复用「不占设备、直接起线程」的现有调度。执行器按冻结的编排选择适配器：

- `sop`：保持现有 `run_bound_sop`。
- `goal`：把编写者和验收者装成 AgentScope `GoalPipeline`，输入是一个模块的材料。
- `team`：队长加预登记成员装成 `TeamPipeline`。成员说明写入分派工具描述。成功条件是每个模块都有名称、边界、测试点和不覆盖范围。

平台不重写退回次数、成员并发或上下文隔离。

### 5. 工具在现有目录上再加种类过滤

设备工具继续走 adb 门面。用例库与只读文档、检索各自登记成新的工具域后，才能被对应种类选中。种类过滤在名片勾选之后，不把允许的工具硬编码进提示词。

### 6. 报告与 BUG 只读冻结列

报告清单仍用一份 HTML 的 `report_run/report_name`。种类、设备、用例名和模块数量从任务冻结列与结果摘要读取，不扫磁盘。BUG 增加 `requirement_breakdown`，分类优先读 `Task.kind`，空值才回退 `task_kind`。登记失败仍只记日志。

### 7. 前端按编排切换，不复制弹窗

工作流配置弹窗先选三对之一，再渲染该编排的名片字段。任务弹窗按冻结种类渲染输入。任务表新增编排与种类两列。卡片展示字段仍由当前名片现算，不写入工作流表。

## 模块防火墙自检

- `ai_assistant` 拥有工作流写操作，只经自己的 `api.py`。
- `task_list` 只读工作流 Model 或 `ai_assistant.api` 来解析名片；任务写操作仍在 `task_list.api`。
- `bug_manager` 与 `report_generator` 只读 `Task` 和纯函数，不导入 runner 或 views。
- `engines/backend_bridge` 只接收已经解析好的绑定、输入和工具，不导入 Django，不写库。
- 前端只走现有 `/api/ai/sop-workflows/` 与 `/api/tasks/`，不新增跨模块直连。

## Risks / Trade-offs

- [AgentScope 流水线接口处于实验阶段] → 适配器只包一次官方调用，调用细节集中在一个模块，官方接口变化时不扩散到 View。
- [旧任务没有冻结列] → 迁移给 `assistant_sop` 回填 `sop + ui_automation`；缺工作流编号时保留现有回溯，不猜种类。
- [Team 产物不稳定] → 模块清单先做结构化校验，不合法就整次失败；不自动生成用例。
- [工具域尚未覆盖用例库和文档检索] → Goal 与 Team 的实现任务先补目录，再允许创建对应工作流。

## Migration Plan

1. 先加可空列和白名单，只开放 `sop + ui_automation`，确认现有创建、排队、重跑不变。
2. 回填旧任务后，把三列改为必填。
3. 工具域就绪后依次开放 Goal、Team。任一步失败时，新组合入口关闭，已创建的 UI 任务仍按旧执行器运行。
4. 回退只停用新组合并保留新列，不删除历史任务、报告或 BUG。
