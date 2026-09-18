## 1. 后端：契约字段与平台工具同步

- [x] 1.1 `apps/ai_assistant/serializers.py` 的 `AgentInputSerializer` 新增 `platform_tools`（`ListField(child=CharField(), required=False, allow_empty=True)`）——验证 `python manage.py check` 与 `ruff check apps/ai_assistant` 通过
- [x] 1.2 `apps/ai_assistant/api.py` 新增 `sync_platform_tools(agent, names)`（仅 `tool_type='platform'`：删除未勾选、创建缺失、置回启用；名字按 `TOOL_SCHEMAS` 过滤），并在 `update_agent` 中接住 `platform_tools` 调用——验证 shell 连续调用两次记录数不变（幂等）、空列表清空 platform 记录、MCP/Skill 记录不受影响
- [x] 1.3 数据回填：`python manage.py migrate_platform_tools --dry-run` 确认范围后实际执行——验证智能体 #10 的平台工具记录数 = 26，且 `_resolve_enabled_tools` 结果包含 `save_case` 与 `save_api_test_case`

## 2. 前端：编辑模式持久化

- [x] 2.1 `frontend/src/modules/ai-assistant/AgentDetail.vue` `save()` 编辑模式写 `payload.platform_tools = [...selectedPlatformTools.value]`（保留 `delete payload.tools` 不变）——验证 Vite dev 编译 200（沙箱禁 esbuild 子进程，`npm run build` 无法在本环境运行，已在任务 3.2 中登记）

## 3. 端到端与门禁

- [x] 3.1 端到端：在智能体 04 的对话中请求创建 TC-NAV-004（挂目录 id=1、priority P1、与 TC-NAV-001 同格式），确认模型调用 `save_case`；若模型未调用工具则回退 handler 直建（同一代码路径）——验证 `cm_test_definitions` 存在 TC-NAV-004、directory_id=1、steps 通过 `validate_steps` 校验
- [x] 3.2 全部门禁：`python manage.py check` + `ruff check apps/ai_assistant` + `python tools/gen_arch_stats.py --check-boundaries` 全绿；前端构建经 Vite dev 编译 200 验证（`npm run build` 因沙箱禁 esbuild 子进程无法在本环境运行，需在普通终端复核）
- [x] 3.3 `openspec archive persist-agent-platform-tools` 归档本 change
