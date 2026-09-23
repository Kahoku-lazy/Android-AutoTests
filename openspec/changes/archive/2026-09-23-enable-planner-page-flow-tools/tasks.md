## 1. 引擎：给 planner 装配页面流工具

- [x] 1.1 `engines/ai/agentscope/config.py` 把 `DEVICE_PLANNER_TOOLS` 由 `[]` 改为 `["list_page_flows", "get_page_flow"]`，并把「规划模型不再读取页面流」的注释改为说明其用途（读页面流文档），验证：`python -m ruff check engines/ai/agentscope/config.py` 通过

## 2. 提示词同步（DB 数据）：让 planner 被告知去读页面流

- [x] 2.1 更新 `apps/ai_assistant/migrations/0038_aiagent_device_prompts.py` 的 `_SNAPSHOT_PLANNER`：在「步骤要求」第 7 条后追加第 8 条指引（`list_page_flows` 看有哪些页面流、`get_page_flow` 取细节），验证：种子文本含 `list_page_flows` 且不含不存在的参数
- [x] 2.2 新增 `apps/ai_assistant/migrations/0041_*.py`：对 `ai_agents.prompt_planner` 做**短语级条件插入**——仅当字段含平台原文锚点（第 7 条）且尚未出现 `list_page_flows` 时追加该条；reverse 删除该条，验证：`python manage.py makemigrations --check --dry-run` 无遗漏；迁移后库内 planner 提示词含指引，且用户改写过的提示词保持原样

## 3. 测试

- [x] 3.1 新增 `tests/graybox/unit/test_ai_role_tool_subsets.py`：断言 planner / executor / verifier 三个子集都 ⊆ `TOOLS` 键集合（静默跳过缺失名的守卫）；planner 恰为这两个页面流工具；`PlannerRole._select_tools` 能从全量工具中选出这两者；executor 子集不含页面流工具、verifier 仍只有 `screenshot_page`，验证：`python -m pytest tests/graybox/unit/test_ai_role_tool_subsets.py -q` 通过
- [x] 3.2 在 `tests/graybox/unit/test_device_prompts.py` 补迁移逻辑用例（纯函数、零 DB 写）：含锚点→插入、已含指引→幂等不重复、无锚点（用户改写）→不变、反向可还原、0038 种子含指引，验证：`python -m pytest tests/graybox/unit/test_device_prompts.py -q` 通过

## 4. 门禁

- [x] 4.1 后端门禁：`python manage.py check`、`python -m ruff check`（改动文件）、`python -m ruff format --check`（改动文件）、`python -m pytest tests/graybox/unit -q`、`python tools/gen_arch_stats.py --check-boundaries`，验证：全部通过、边界零违规
