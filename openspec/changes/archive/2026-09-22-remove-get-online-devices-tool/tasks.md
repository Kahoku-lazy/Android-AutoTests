## 1. 后端：从工具注册表移除

- [x] 1.1 `apps/ai_assistant/tools.py` 删除 `get_online_devices` 函数、`TOOLS` 条目与 `TOOL_META` 条目（保留 `acquire_device`/`list_devices` 等其余条目），验证：`python -m ruff check apps/ai_assistant/tools.py` 通过，且 `get_tool_debug_schema("get_online_devices")` 抛 `ToolNotFoundError`
- [x] 1.2 `engines/ai/agentscope/config.py` 从 `VISION_TOOLS` 删除该条目，验证：`python -m ruff check engines/ai/agentscope/config.py` 通过，且 `VISION_TOOLS` 与删后的 `TOOLS` 键集合交集中不再有该名

## 2. 提示词同步（DB 数据）

- [x] 2.1 更新 `apps/ai_assistant/migrations/0038_aiagent_device_prompts.py` 的两处种子文本（executor / verifier），验证：该文件内不再出现 `get_online_devices`
- [x] 2.2 新增 `apps/ai_assistant/migrations/0039_*.py`：forward 对 `ai_agents.prompt_executor` / `prompt_verifier` 做短语级条件替换（不含原文短语则跳过），reverse 反向替换，验证：`python manage.py makemigrations --check --dry-run` 无遗漏；对存量库执行 `python manage.py migrate ai_assistant` 后，Agent 10 的 executor/verifier 中不再含该名，且**人工构造的"用户已改写"提示词保持原样**

## 3. 手册与前端常量

- [x] 3.1 `engines/ai/skills/platform-tools-manual/SKILL.md`：删该表格行；数量改为「12 个」；分类改为 设备管理 8 + 设备检查器 1 + **视觉识别 1（含 ocr_page）** + 工作流 2；同步 frontmatter description、链路归属（VISION_TOOLS 说明）与第九条查询工具清单，验证：手册内不再出现该工具名，且各分类条目数与标题数字一致
- [x] 3.2 `frontend/src/modules/ai-assistant/constants.ts` 从 `PLATFORM_TOOL_NAMES` 删除该条目，验证：`cd frontend && npm run typecheck` 通过

## 4. 测试与 spec 同步

- [x] 4.1 `tests/graybox/unit/test_ai_platform_tool_debug.py`：把 4 处用它当"无参只读工具"的用例（无参 schema、未知参数、user_id 注入、HTTP 只读调用）改用 `list_devices`，验证：`python -m pytest tests/graybox/unit/test_ai_platform_tool_debug.py -q` 通过
- [x] 4.2 `frontend/tests/ai-assistant/p0/useToolDebug.spec.ts` 与 `ToolboxPanel-tool-debug.spec.ts` 改用 `list_devices` / `list_apps`（后者保持两张工具卡与"停用卡仍有调试入口"的断言语义），验证：`cd frontend && npx vitest run tests/ai-assistant` 通过
- [x] 4.3 spec delta 的「无参只读工具执行成功」场景样例已由该工具改为 `list_devices`，验证：`openspec validate remove-get-online-devices-tool --strict` 通过

## 5. 全仓一致性校验与门禁

- [x] 5.1 全仓检索该工具名，确认仅剩允许的命中（`apps/device_pool/api.py` 的同名内部函数及其调用方、`openspec/changes/archive/**` 历史归档、历史迁移 0038 已由 2.1 清理），验证：`git grep -n get_online_devices` 输出逐条可解释
- [x] 5.2 后端门禁：`python manage.py check`、`python -m ruff check`（改动文件）、`python -m pytest tests/graybox/unit -q`，验证：全部通过
- [x] 5.3 前端门禁：`cd frontend && npm run lint:styles && npm run typecheck && npx vitest run tests/ai-assistant`，验证：全部通过，无新增 vue-tsc 错误
