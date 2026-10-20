## Why

控制设备任务已经只启动 `engines/agents` 的 SOP，但 Django 仍在导入 `engines/ai` 的模型协议，旧的规划 / 执行 / 验收工作流和三条管理命令还留在仓库里。现在删掉这套旧引擎，避免启动路径继续绑在已经不用的代码上。

## What Changes

- **BREAKING** 删除 `engines/ai` 整包。不再提供 `TaskRequest` / `get_ai_engine`，也不再跑规划模型生成步骤。
- 控制设备任务仍按现有 SOP 启动。执行与验收模型继续从控制设备线路读取，在平台侧组装后交给 SOP，不经过旧引擎。
- 执行或验收的模型名、密钥、provider 不合法时，任务在启动阶段失败。不再要求规划角色存在。
- **BREAKING** 删除管理命令 `model_test`、`planner_eval`、`ui_pipeline`，以及 `model_assembly.py`。
- **BREAKING** 共享技能的落盘与扫描根从 `engines/ai/skills` 改为 `engines/agents/skills/shared`。该目录现在不存在，实施时创建空目录。SOP 仍只从 `engines/agents/skills/executor` 挂角色技能，不把 `common` / `executor` 扫进共享工具箱。
- 收回只由旧引擎满足的需求：旧引擎协议、平台三模型任务、规划模型的页面流工具、旧引擎里由规划结果驱动的执行/验收步骤、旧引擎的三角色过程日志，以及「SOP 脚手架不得改平台引擎目录」这条限制。
- 收回执行 / 验收提示词必须放在 `engines/ai/agents/config.py` 的需求。任务详情对执行结果与验收结果的展示需求保持不变。

## 关联文档

PRD-08。本单删除该需求里已被 SOP 替代的旧规划引擎，无单独子编号。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ai-shared-skill-upload`: 共享技能目录改为 `engines/agents/skills/shared`。
- `sop-task-run`: 启动时直接组装执行与验收模型，不经过旧引擎；配置不合法则任务失败。
- `ai-engine-protocol`: 收回旧引擎协议的全部需求。
- `ai-platform-task`: 收回平台任务的三模型工作流。
- `ai-device-planner-tools`: 收回规划模型读取页面流的需求。
- `ai-executor-verifier-sop`: 收回由规划结果驱动的旧步骤编排。
- `ai-executor-output`: 收回「执行提示词必须在旧引擎常量文件」；详情展示保留。
- `ai-verifier-output`: 收回「验收提示词必须在旧引擎常量文件」；详情展示保留。
- `ai-agent-process-log`: 收回旧三角色过程日志。运行日志仍由现有 `agent_events.log` 承担。
- `agent-sop-runner`: 收回「不得修改平台侧旧引擎目录」。

## Impact

- 后端：`apps/ai_assistant/engine_adapter.py`、`task_runner.py`、`skills_catalog.py`、工具箱上传；删除 `model_assembly.py` 与三条管理命令。
- 引擎：删除 `engines/ai/**`。`engines/agents` 的 SOP、工具与 `executor` 技能目录保持现有装配方式。`ToolSpec` 仍在 `engines/agents/tools/tool_base.py`。
- 前端：无页面改版。共享技能上传成功后的文件落在新目录。
- 测试：删除或改写只覆盖旧引擎的测试；保留 SOP 启动、技能上传目录、模型配置失败这几条。不跑全量回归。
- 不改：任务详情里执行结果与验收结果的展示字段、设备工具、日志检查工具、同设备排队。
