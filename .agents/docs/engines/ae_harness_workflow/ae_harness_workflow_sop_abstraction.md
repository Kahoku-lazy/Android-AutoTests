# ae_harness/workflow · 多角色编排抽象
> 归属模块：`engines/ae_harness/workflow` ｜ 类型：引擎模块开发说明
> 代码真相源：`engines/ae_harness/workflow/sop/spec.py`、`engines/ae_harness/workflow/sop/runner.py`、`engines/ae_harness/workflow/goal.py`、`engines/ae_harness/workflow/team.py`
> 上级约束：engines/AGENTS.md ｜ 模块索引：engines/AGENTS.md

## 定位：只有抽象，没有装配

| 位置 | 是什么 | 谁能用 |
| --- | --- | --- |
| `sop/spec.py`、`sop/runner.py` | **通用的 SOP 抽象**：步骤模型、从调用方给的 YAML 加载、编排执行 | 任何调用方 |
| `goal.py` | **目标流水线抽象**：执行者产出、验收者判定、退回重做 | 任何调用方 |
| `team.py` | **团队流水线抽象**：队长分派、成员完成 | 任何调用方 |

本目录不建角色、不挂工具、不读命令行。控制台装配 `sop_runner.py` 已删除。

**平台（后端任务 / 前端卡片）的装配在 [`engines/backend_bridge/workflow/`](../backend_bridge/backend_bridge_role_assembly.md)**：它准备好两个角色和步骤，再调用本目录的 `load_spec` / `run_sop`。步骤内容由调用方提供，不在本目录维护流程。

## 职责

把**多个角色**按流程串起来。三条链路都只消费调用方给的角色，不建角色、不存流程：

```text
workflow/
  sop/
    spec.py           StepSpec / SopSpec / load_spec
    runner.py         build_sop / run_sop / SopResult
  goal.py             run_goal / GoalResult
  team.py             run_team / TeamRole / TeamResult
```

调用方式：

```python
from engines.ae_harness.workflow.sop import load_spec, run_sop

spec = load_spec(steps_path)  # 步骤文件由调用方提供
result = await run_sop(executor, verifier, spec, log_dir=LOG_DIR)

goal = await run_goal(executor, verifier, task, log_dir=LOG_DIR)
team = await run_team(leader, members, task, log_dir=LOG_DIR)
```

## 步骤 YAML

```yaml
name: ui-task
description: 按里程碑推进手机 UI 任务。
task: 回到桌面，然后打开设置

steps:
  - subject: 回到桌面
    description: 设备停在桌面，能看见 dock 和桌面图标。
    max_attempts: 3
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `name` | 是 | 流程名 |
| `steps` | 是 | 非空列表，按顺序执行 |
| `steps[].subject` | 是 | 步骤名 |
| `steps[].description` | 是 | 这一步必须达成的结果，只写终点不写路线 |
| `steps[].max_attempts` | 否 | 默认 3 |
| `task` | 否 | 交给第一步的任务描述，不填则用 `name` |
| `description` | 否 | 流程用途说明 |

## 红线（AI 禁止事项）

1. **禁止在 `workflow/` 建角色或挂工具** —— 执行者与验收者由调用方建好传入；本目录不调 `create_agent`、不 `add_tool`。
2. **禁止绕过 `run_sop` 自己写编排循环** —— 步骤推进、重试预算、驳回记录都由 SOP 引擎负责，不要在别处重写一遍。
3. **禁止把步骤写死在 Python 里** —— 步骤是调用方给的数据；本目录只定义字段，不保存具体流程。
4. **禁止在 `workflow/` 拼 HTML** —— 报告一律走 `event/` 的 `HtmlReportRenderer`。
5. **禁止在 `workflow/` 读提示词或造模型** —— 提示词正文与连接参数由调用方在 `backend_bridge` 准备；本目录只消费已经建好的角色。
6. **禁止在本目录决定验收者的工具** —— 谁挂只读工具由调用方装配，本目录不 `add_tool`。

## 已知限制

1. 本目录不从任务文本拆步骤；步骤由调用方准备好后传入。
2. 报告里「执行者 / 验收者」的归属优先按 `run_sop` 传入记录器的名字映射（agent 名 → 角色）判定，不依赖回复顺序；未传映射的调用方仍沿用奇偶推断（每步第一次 reply 是执行者，第二次是验收者）。尝试序号取自官方 `SOP_STEP_STARTED` 事件的 `attempt` 字段，落进工具记录。
3. SOP 模块在 AgentScope 2.0.12 里仍标为实验性，升级前需复核 `SOPStep.reply_stream` 的调用顺序。
