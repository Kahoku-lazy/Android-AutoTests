## 1. 工作流包与运行类

- [x] 1.1 新增 `engines/agents/workflow/`，把 `SopRunner` 从 `engines/agents/role/sop.py` 移到 `workflow/runner.py`。构造参数仍只接收已装配的 `SOP`。`dump_state` 只导出 `SOPRunState`。删掉直接把步骤 `phase` 写成 `FAILED` 的停步逻辑。验证：`rg -n "class SopRunner" engines/agents/workflow/runner.py` 能命中；同文件没有 `phase = SOPPhase.FAILED`。
- [x] 1.2 `workflow/__init__.py` 导出 `SopRunner`。验证：`python -c "from engines.agents.workflow import SopRunner"` 成功。

## 2. 步骤输入与装配

- [x] 2.1 在 `workflow/steps.py` 增加 `SopStepInput` 和 `SopSteps`。`subject` 是步骤短名，`description` 只写必须达成的结果。`build()` 在步骤为空、任一步缺字段，或执行/验收角色尚未 `start()` 时拒绝装配；成功时按输入顺序生成 `SOP`，每步使用这两个角色的 Agent，且不改写角色提示词、工具包和技能。验证：新增 `tests/graybox/unit/test_sop_steps.py`，覆盖完整步骤成功、空列表或空字段失败、未启动角色失败；`python -m pytest tests/graybox/unit/test_sop_steps.py -q` 通过。
- [x] 2.2 装配出的步骤在一次尝试内部接住「日志为空」，调用 `record(passed=False, message=日志为空)` 后把这次尝试正常交还引擎。次数未用尽时该步回到待重做；次数用尽时由引擎标失败。验证：改写 `tests/graybox/unit/test_sop_log_empty_abort.py`，分别覆盖「上限为 2 时第一次日志为空后运行阶段不是失败」和「连续驳回达到上限后阶段为失败且结论条数等于上限」；`python -m pytest tests/graybox/unit/test_sop_log_empty_abort.py -q` 通过。
- [x] 2.3 `__init__.py` 同时导出 `SopStepInput` 与 `SopSteps`。手工入口移到 `runner.py` 的 `__main__`：示例步骤先 `SopSteps.build()`，再交给 `SopRunner`。验证：`rg -n "SopSteps|SopRunner" engines/agents/workflow/runner.py` 能看到这个顺序，且 `workflow` 目录下没有 `prompt_config` 或 `tools_config` 的 import。

## 3. 迁出角色目录

- [x] 3.1 删除 `engines/agents/role/sop.py`。测试改为从 `engines.agents.workflow` 导入。验证：`rg -n "role.sop|role/sop" engines tests` 无匹配；`python -m pytest tests/graybox/unit/test_sop_log_empty_abort.py tests/graybox/unit/test_sop_steps.py -q` 通过。
- [x] 3.2 在 `engines/agents/AGNETS.md` 的文件夹说明中增加 `workflow`：存放 SOP 步骤输入与单次运行，不在此创建角色或配置提示词、工具。验证：`rg -n "workflow" engines/agents/AGNETS.md` 能看到该条，且 `ruff check engines/agents/workflow engines/agents/role/executor.py` 无新增问题。
