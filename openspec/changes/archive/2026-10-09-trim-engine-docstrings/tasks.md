## 1. 改写注释（已实施）

- [x] 1.1 引擎协议与实现：`engines/ai/__init__.py`、`base.py`、`engine.py`、`registry.py` 按「功能 / 入参 / 返回值」重写；`LogEvidenceProvider` 的 `open_window` / `read_window` 补齐 `Args:` / `Returns:` / `Raises:`
- [x] 1.2 智能体包：`agents/__init__.py`、`agents/base.py`、`agents/config.py`、`agents/executor.py`、`agents/planner.py`、`agents/verifier.py`；`RoleSpec` / `AgentRole` / `create_model` / `build_device_models` 只留职责与契约，删设计要点与边界讨论
- [x] 1.3 消息与事件：`messaging/__init__.py`、`events.py`、`messages.py`；删「唯一解析归属」「后续变更将替换」等旁白，`RoleResult` 收为一句职责
- [x] 1.4 计费与过程日志：`billing/__init__.py`、`billing.py`、`usage.py`、`process_log.py`；保留价目同步与按天切分等格式约定，删"为什么单独一个模块"整段
- [x] 1.5 工具包：`tools/__init__.py`、`tool_device.py`、`tool_device_catalog.py`；**未动**登记清单里的工具说明书字面量
- [x] 1.6 工作流包：`workflow/__init__.py`、`workflow.py`、`sop_step.py`、`logcheck.py`、`evidence.py`；删「改造前逐字一致」「对象协作自下而上」「任务链路唯一真相源」等设计旁白，保留点击证据配对、日志等级、失败语义等契约
- [x] 1.7 明确不改：`engines/ai/skills/skill-creator/**`（vendored）、`agents/config.py` 的提示词常量、全部字符串字面量

## 2. 验证（已执行）

- [x] 2.1 `python -m ruff check engines/ai` → `All checks passed!`
- [x] 2.2 `python -m ruff format --check engines/ai` → `26 files already formatted`（无需重排）
- [x] 2.3 `python -m pytest tests/graybox/unit -q -k "agent or workflow or engine or device or tool or screenshot"` → 362 passed / 1 failed；唯一失败是 `test_workflow_single_path.py::test_frontend_api_layer_has_no_legacy_create_paths`（读前端源码的存量红，与本单无关）
- [x] 2.4 代码逻辑零变化：`temps/compare_code_ast.py temps/before_ai engines/ai` → 剥离 docstring 与属性文档后，36 个文件全部一致
- [x] 2.5 自查统计（非 vendored）：docstring 703 行 → 654 行；`>= 4 行` 的 docstring 75 处 → 65 处（剩余均为确实需要 `Args:` / `Returns:` 的）
- [x] 2.6 旁白关键词扫描（`temps/scan_narration.py`）：剩余命中项经逐条复核，全部是行为语义（如"同名注入条目被跳过"），不含设计理由 / 历史沿革 / 消费者说明

## 3. 归档（不在本单执行，由仓库维护者接手）

- `skip_specs: true`：纯注释整理、无需求级变化，归档时无需并入主规格，也不移动目录。
