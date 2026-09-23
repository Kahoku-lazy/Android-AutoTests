## 1. 后端：候选登记与解析

- [x] 1.1 在 `apps/ai_assistant/tools.py` 登记「工具名 → 参数名」候选表，覆盖 `list_apps` / `device_action` / `click_ratio` / `drag_ratio` / `xpath_action` 的 `serial`，并让 `get_tool_debug_schema()` 为命中项输出候选声明（函数保持纯反射，不引入 `user_id`），验证：`pytest tests/graybox/unit/test_ai_platform_tool_debug.py -q` 通过，且新增用例断言这 5 个工具的 `serial` 带候选声明、`acquire_device` 与 `release_device` 的 `serial` 不带
- [x] 1.2 在 `apps/ai_assistant/views_tool_debug_drf.py` 的 schema 视图解析候选：经 `apps/device_pool/api.py::list_devices(user_id)` 取数，过滤「`status` 为 ONLINE 且 `occupied_by` 为空」，映射为含可提交取值与可读标签的候选项后填入参数字段，验证：单测断言非超级管理员的候选等于其可见且在线未被占用的设备集合，且候选中不含使用中或被执行引擎占用的设备

## 2. 前端：下拉控件

- [x] 2.1 `frontend/src/modules/ai-assistant/api/toolbox.ts` 扩展参数字段以承载候选清单（可提交取值 + 可读标签），验证：`cd frontend && npm run typecheck` 通过
- [x] 2.2 `composables/useToolDebug.ts` 保持 `defaultFormValues()` 与 `buildParams()` 对候选参数的行为不变（仍按 `type` 取值、空值且非必填则省略），候选为空时不阻断提交，验证：`npx vitest run tests/ai-assistant/p0/useToolDebug.spec.ts` 通过，含新增用例「候选为空仍可提交手输值」
- [x] 2.3 `ToolDebugPage.vue` 为带候选的参数渲染 `el-select`（`filterable` + `allow-create`），候选为空时给行内提示且不禁用执行，验证：`npm run typecheck` 通过，并手工走查 `device_action` 调试页（可选在线设备、可手输、无候选设备时仍能提交）

## 3. 门禁与文档

- [x] 3.1 后端门禁：`python manage.py check`、`ruff check apps/ai_assistant`、`ruff format --check apps/ai_assistant`、`pytest tests/graybox/unit/test_ai_platform_tool_debug.py -q`，验证：全部通过
- [x] 3.2 前端门禁：`cd frontend && npm run lint:styles && npm run typecheck && npm run test`，验证：全部通过，无新增 vue-tsc 错误
- [x] 3.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries`，验证：通过，并人工确认 `ai_assistant` 未 import `device_pool` 的 models/service/state_machine/views，只经其 `api.py` 取数
- [x] 3.4 文档同步：AI 助手接口文档登记 schema 新增的候选字段与候选口径；模块 `AGENTS.md` 增补调试页设备下拉行为，验证：`python tools/gen_arch_stats.py --check-md` 通过
