## Context

见 proposal.md - Why。当前流程装配函数 `build_device_sop` 与运行类 `SopRunner` 都在 `engines/agents/role/sop.py`。执行角色与验收角色的提示词、工具包和技能已经在 `engines/agents/role/executor.py` 里配好，并在 `start()` 时写进 Agent。`tests/graybox/unit/test_sop_log_empty_abort.py` 直接导入 `SopRunner`。

## Goals / Non-Goals

**Goals:**

- 工作流分成两个类：步骤类负责输入格式和装配，运行类只接收装配结果并推进。
- 步骤类只取已启动角色上的 Agent，不读取或覆盖 `executor.py` 里的提示词、工具包和技能。
- 运行类保留事件上屏、对话稿和按次计费。状态只导出 `SOPRunState`。日志为空走引擎的一次驳回，次数用尽后才由引擎标失败。

**Non-Goals:**

- 不改执行角色、验收角色的提示词、工具分组或 ReAct 默认值。
- 不把旧 `engines/ai` 工作流的日志开窗、截图回填或 Pydantic 交接搬过来。
- 不在 `role` 包保留兼容导入。

## Decisions

### 1. 目录与两个类

新增 `engines/agents/workflow/`：

- `steps.py`：`SopStepInput` 表示一步输入。`subject` 是步骤短名，`description` 只写必须达成的结果。`SopSteps` 接收已启动的执行角色、验收角色、步骤列表、流程名和每步重试上限；`build()` 校验输入并返回框架 `SOP`。
- `runner.py`：把现有 `SopRunner` 移入。构造参数仍是已经 `build()` 的 `SOP`，不接收原始步骤列表。`dump_state` / `resume_from` 只读写 `SOPRunState`，不保存两个 Agent 的上下文。
- `__init__.py` 导出 `SopStepInput`、`SopSteps`、`SopRunner`。

「处理步骤后传入第三步」落成调用顺序：角色沿用 `executor.py` 的配置并 `start()`，`SopSteps.build()` 产出流程，再把该流程交给 `SopRunner`。

备选是继续用一个函数 `build_device_sop` 加 `SopRunner`。函数没有地方声明输入格式，调用方仍要传裸元组，所以改成步骤类。

### 2. 角色配置只从已启动角色读取

`SopSteps.build()` 沿用现在的 `_require_agent`：角色的 `agent` 为空就失败。执行与验收 Agent 来自 `ExecutorRole.start()` / `VerifierRole.start()`，因此系统提示词、工具包、技能、多模态和 `RoleConfig` 默认的 ReAct、上下文配置已经在 Agent 上。工作流不 import `prompt_config` 或 `tools_config`。

备选是在工作流里重新 `ExecutorRole(config)`。那会让工作流拥有第二份装配入口，和「配置只在 executor.py」重复。

### 3. 日志为空记成引擎的一次驳回

现在 `SopRunner._stop_for_tool` 自己追加 `VerificationResult` 并把步骤 `phase` 写成 `FAILED`，一次日志为空就结束整次运行，引擎的 `max_attempts` 不参与。

改为在这一次尝试内部接住该异常，调用步骤的 `record(passed=False, message=日志为空, verifier="sop")` 后正常结束这次尝试。`record` 会清空交付并把步骤设回 `PENDING`。随后由 `SOPEngine` 决定：次数未用尽就带着这条说明重做同一步，次数用尽才把该步标为 `FAILED`。运行器不再写 `phase = FAILED`。

接住异常的位置必须在 `SOPStep.reply_stream` 之内。异常若冒出 `SOPEngine.reply_stream`，引擎来不及做次数判断。实现上用一个只包这一处的 `SOPStep` 子类，其余仍走框架的执行与验收。

备选是在运行器里接住异常后再调用 `reply_stream(None)`。引擎只在一次尝试正常返回后检查次数，中途异常后再进入会把已用尽的步骤又启动一轮。

### 4. 示例步骤与手工入口跟着工作流走

现在文件顶部的 `DEVICE_SOP_STEPS` 和 `__main__` 手工运行移到 `runner.py`。示例步骤改成 `SopStepInput` 列表，经 `SopSteps.build()` 再交给 `SopRunner`。`role/sop.py` 删除。

### 5. 目录说明

`engines/agents/AGNETS.md` 的文件夹说明增加 `workflow`：存放 SOP 步骤输入与单次运行，不在此目录创建角色或配置提示词、工具。

## 模块防火墙自检

- 不新增跨 App import。工作流只依赖本包的 `role`、`messaging`、`billing`，以及既有的 AgentScope。
- 不写数据库，不经过 `api.py`，不触达前端。
- 不 import 其他 App 的 service、runner、consumer 或状态机。

## Risks / Trade-offs

- [调用方仍从 `engines.agents.role.sop` 导入] → 本次明确删除该模块，并改掉仓库内唯一的测试导入。不留转发模块，避免角色目录再次装进工作流。
- [日志为空仍被运行器直接写成失败] → 停步测试改成两档：次数未用尽时步骤回到待重做且运行未失败；次数用尽时由引擎标失败，结论条数等于上限。

## Migration Plan

1. 新增 `workflow` 包并移入运行类。
2. 用 `SopSteps` 替换 `build_device_sop`。
3. 删除 `role/sop.py`，更新测试导入与目录说明。
4. 回退时恢复 `role/sop.py`，并删除 `workflow` 包。无数据迁移。
