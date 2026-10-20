## 1. 切断任务启动对旧引擎的导入

- [x] 1.1 `engine_adapter.sop_role_models` 直接构造 SOP 的 `ModelConfig`，删除对 `engines.ai.base` 的导入，以及只服务旧引擎的 `build_request`。`resolve_device_serial` 保留。验证：`python -m pytest tests/graybox/unit/test_task_runner_sop.py -q` 通过，且 `engine_adapter.py` 中不再出现 `engines.ai`。
- [x] 1.2 为启动组装补测试：没有规划角色时仍返回执行与验收模型；模型名为空、密钥为空或 provider 不是 DeepSeek 与阿里百炼时抛出可读错误并指出缺失项或非法 provider。验证：`python -m pytest tests/graybox/unit/test_sop_role_models.py -q` 通过。

## 2. 共享技能目录

- [x] 2.1 将 `SHARED_SKILLS_DIR` 改为 `engines/agents/skills/shared`，创建该目录及 Git 可跟踪的占位文件。扫描仍只认该目录下一级且含 `SKILL.md` 的文件夹。验证：`python -m pytest tests/graybox/unit/test_ai_shared_skill_upload.py -q` 通过，且仓库中不存在 `engines/ai/skills`。
- [x] 2.2 补一条扫描测试：`common` 与 `executor` 下的技能不出现在共享扫描结果中。验证：该测试在 `python -m pytest tests/graybox/unit/test_ai_shared_skill_upload.py -q` 中通过。

## 3. 删除旧引擎及其专用入口

- [x] 3.1 删除 `model_test`、`planner_eval`、`ui_pipeline` 与 `model_assembly.py`。验证：`python manage.py help` 不再列出这三条命令，且全仓库 `*.py` 不再导入 `model_assembly`。
- [x] 3.2 删除只为旧引擎存在的测试；仍覆盖 SOP、设备日志或技能上传的测试改为不导入 `engines.ai`。`test_task_runner_sop` 改为断言任务启动代码路径不导入 `engines.ai`，不再补丁 `engines.ai.registry`。验证：`python -m pytest tests/graybox/unit/test_task_runner_sop.py tests/graybox/unit/test_sop_role_models.py tests/graybox/unit/test_ai_shared_skill_upload.py -q` 通过。
- [x] 3.3 删除 `engines/ai` 整包，包括只做转发的 `tools_base.py`。验证：目录不存在，且 `python -c "from engines.agents.tools.tool_base import ToolSpec; from engines.agents.tools_config import build_executor_toolkit"` 成功。

## 4. 注释与排除规则

- [x] 4.1 更新 `skills_catalog.py`、`api.py`、`tools.py`、`views_toolbox_drf.py`、`engines/__init__.py`、`config/settings.py` 中仍指向旧引擎或旧技能目录的说明。`ruff.toml` 与 `tools/check_gates.py` 去掉对已删除 `engines/ai/skills` 的排除。验证：`python -m ruff check apps/ai_assistant/engine_adapter.py apps/ai_assistant/skills_catalog.py engines/agents/tools/tool_base.py` 通过，且 `rg "engines\.ai|engines/ai" --glob "*.py" --glob "*.toml"` 无匹配。

## 5. 收口

- [x] 5.1 确认 Django 能加载、SOP 工具箱能装配。验证：`python manage.py check` 通过，且第 3.3 与第 4.1 的命令再次通过。不跑全量回归。
