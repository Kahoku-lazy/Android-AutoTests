# engines/ae_harness/workflow AGENTS.md

## 定位：抽象层 + 一个控制台装配

| 位置 | 是什么 | 谁能用 |
| --- | --- | --- |
| `sop/spec.py`、`sop/runner.py`、`sop/steps/*.yaml` | **通用的 SOP 抽象**：步骤模型、加载、编排执行、步骤 YAML | **任何调用方**——控制台、平台都从这里调用 |
| `sop_runner.py` | **控制台装配**：读命令行、建两个角色、打印结论 | 只服务控制台调试 |

`sop/` 不属于控制台，它是被复用的地基；换一个调用方（例如平台）只是换装配方式，不重写抽象。

**平台（后端任务 / 前端卡片）用的执行 + 验收 SOP 在 [`engines/backend_bridge/workflow/`](../../backend_bridge/AGENTS.md) 新建装配**，由它调用本目录 `sop/` 的 `load_spec` / `run_sop`。

判断：要人盯着终端看 → 用 `sop_runner.py`；结果是交给程序 → 在 `backend_bridge/workflow/` 自己装配，但**只调抽象、不复制实现**。

## 职责

把**多个角色**按流程串起来。当前只有 SOP 一条链路：

```text
workflow/
  sop/
    spec.py           StepSpec / SopSpec / load_spec
    runner.py         build_sop / run_sop / SopResult
    steps/*.yaml      流程定义：步骤名 + 必须达成的结果 + 重试次数
  sop_runner.py       命令行入口：读 YAML、建两个角色、跑流程、打印结论
```

调用方式：

```python
from engines.ae_harness.workflow.sop import load_spec, run_sop

spec = load_spec(Path("steps/ui_task.yaml"))
result = await run_sop(executor, verifier, spec, log_dir=LOG_DIR)
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
3. **禁止把步骤写死在 Python 里** —— 步骤是数据，只放 `steps/*.yaml`；代码里只保留默认路径。
4. **禁止在 `workflow/` 拼 HTML** —— 报告一律走 `event/` 的 `HtmlReportRenderer`。
5. **禁止给验收者传带写操作的工具集** —— 验收侧必须是 `build_adb_readonly_tools()`。
6. **禁止在 `workflow/` 读模型配置或提示词** —— 那些只能经 `agents/config.py`；步骤 YAML 属于流程数据，允许在本目录读。

## 已知限制

1. 步骤 YAML 目前手写，没有从任务文本自动拆分的逻辑。
2. 报告里「执行者 / 验收者」的分块靠 reply 顺序推断（每步第一次 reply 是执行者，第二次是验收者），依赖 SOP 引擎当前「先执行后验收」的固定结构。
3. SOP 模块在 AgentScope 2.0.9 里标为实验性，升级前需复核 `SOPStep.reply_stream` 的调用顺序。
