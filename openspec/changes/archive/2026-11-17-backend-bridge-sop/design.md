## Context

`engines/ae_harness/workflow/sop/` 已经是一套**通用抽象**（不属于控制台）：

| 原语 | 关键点 | 平台怎么用 |
| --- | --- | --- |
| `load_spec(path)` | 读 YAML → `SopSpec(name, steps, description, task)` | 直接调，用现成步骤文件 |
| `run_sop(executor, verifier, spec, *, log_dir, role, renderer, api_key_env, role_api_keys, observations)` | 内部建 SOP+引擎、跑流、记录事件、渲染报告、汇总每步 | 直接调，只换报告根 |
| `SopResult(phase, steps[StepOutcome], record)` | 每步 `subject/passed/attempts/message` | 整理成返回值 |
| `steps/ui_task.yaml`、`govee_widget.yaml` | 步骤 + 必须达成的结果 | 选一份，用任务文本覆盖 `task` |

控制台侧的装配是 `workflow/sop_runner.py`（读 argv、建两个角色、打印）。平台不能复用它，但**复用同一批抽象**。

对话页当前只有单角色卡（`platform_ui`），本变更**不碰对话模块**。

## Goals / Non-Goals

**Goals:**

- 平台能跑「执行 + 验收」SOP：每步有验收结论，每次运行有报告与用量。
- 编排零自创：步骤、重试、驳回、报告全部走 `ae_harness`。
- 平台侧有一次性触发入口（管理命令），可端到端验证。

**Non-Goals:**

- 不动对话页、不新增对话卡片、不改 `WorkflowListView` / `WorkflowStreamView`。
- 不改 `engines/ae_harness` 任何代码（**包括不给 `run_sop` 加回调**）。
- 不接 `task_list` 任务链路；不做步骤自动拆分。

## Decisions

### D1. 目录与职责：`workflow/roles.py` + `workflow/sop_ui.py`

| 文件 | 只做一件事 |
| --- | --- |
| `workflow/roles.py` | 装配执行者（全量工具）与验收者（只读工具），共用一个观测中间件 |
| `workflow/sop_ui.py` | 一次运行：选流程 → 覆盖 task → `run_sop(log_dir=REPORT_ROOT, …)` → 整理 `SopRunResult` |

拆两个文件，是为了让「角色装配」与「一次运行」各自可测。

### D2. 步骤来源：只用现成 YAML，任务文本只覆盖 `task`

默认 `ui_task.yaml`；调用方可传流程标识（`ui_task` / `govee_widget`）。任务文本写进 `spec.task`，**不生成步骤**。

理由：步骤是「这次必须达成什么」，让模型现拆等于自创验收标准，且报告无法复现。

### D3. 一次运行一套角色

每次调用都新建执行者与验收者，跑完即弃，不跨运行复用。

理由：这与旧的 UI 自动化链路（一次任务跑一整条流程、跑完即弃）一致；也避免上一次运行的操作残留影响下一次的验收判断。

代价：每次多一次角色构建开销（毫秒级）。

### D4. 不引入事件回调

原本想给 `run_sop` 加 `on_event`，让对话页的面板能看 SOP 过程。**对话页不参与本变更，因此不需要**：`run_sop` 已经把过程完整写进 JSONL 与 HTML 报告，事件面板不在本变更范围。

结论：`ae_harness` 零改动，本层也不监听事件流。

### D5. 触发入口用管理命令，与单角色并列

新增 `python manage.py run_ui_sop "<任务>" [--spec ui_task|govee_widget] [--execution-id …]`：

- 跑一次 SOP → 打印每步通过情况与 token → 用量交 `record_run_usages` 入账。
- 与既有 `run_ui_agent`（单角色）并列，二者互不影响。

不走对话页、不走对话接口：对话页的设计只有单角色。

### D6. 返回值与单角色并列，不合并

`sop_ui.py` 返回 `SopRunResult`：

- 共同字段：`report_path`、`log_path`、`model`、`tokens`、`by_api_key_env`、`usages`、`cost_s`
- SOP 独有：`phase`、`steps`（每步 subject/passed/attempts/message）

不合并成万能结果体，避免单角色路径被塞进空的 `steps`。

## 模块防火墙自检

| 红线 | 是否触碰 | 说明 |
| --- | --- | --- |
| 跨 App / 写库 / 前端 | 否 | 本层不引 Django、不写库（命令里由后端写账） |
| `engines/` 零 `django.*` / `apps.*` | 是（遵守） | 导入守卫测试覆盖 |
| 禁止自创 SOP | 是（遵守） | 只调 `load_spec` / `run_sop` |
| 验收者只读工具 | 是（遵守） | 固定 `build_adb_readonly_tools()` |
| 改 `ae_harness` | **否** | 本变更零改动，D4 已说明原因 |

## Risks / Trade-offs

- **每次新建角色**：多一次构建开销；换来运行间互不干扰。
- **报告与单角色同根**：报告历史页按目录列出，新增 SOP 目录会一并出现，无需改动前端。
- **SOP 是 AgentScope 实验特性**：升级前需复核 `SOPStep.reply_stream` 顺序（记在 `workflow/AGENTS.md`）。
- **没有进度反馈**：管理命令只在跑完后打印；如需实时进度，属后续变更。

## Migration Plan

1. 先落 `roles.py` + 单测（只读工具约束）。
2. 再落 `sop_ui.py` + 单测（结果字段、不打印、两次运行互不影响）。
3. 加管理命令，真机跑一次：报告落盘 + 账本新增行。
4. 回滚：删除 `backend_bridge/workflow/` 与 `run_ui_sop.py` 即可，`ae_harness` 与对话页均未改动。

## Open Questions

- 后续是否让 `task_list` 的 UI 自动化任务改走这条 SOP（真正替代 `engines/agents` 的跑量路径）？属独立变更，本变更不做。
