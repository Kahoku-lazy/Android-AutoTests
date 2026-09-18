## 1. 工具 schema 与分发

- [x] 1.1 在 `apps/ai_assistant/tools.py` 增加 `get_tool_debug_schema(name)`：从签名推导参数（剥 `user_id`），返回 name/summary/read_only/parameters；未知名抛约定错误。验证：`pytest tests/graybox/unit/test_ai_platform_tool_debug.py -k schema`（新建，覆盖 `get_online_devices` 无参、`acquire_device` 含 serial、schema 不含 `user_id`、未知名）
- [x] 1.2 同文件增加 `invoke_platform_tool(name, user_id, params)`：丢弃 body 中的 `user_id`、拒绝未知键、按注解做简单类型转换、调用 `TOOLS` 函数并规范化返回。验证：同文件单测 mock 工具函数，断言注入的 `user_id` 来自参数而非 body、多余键报错

## 2. JWT 视图与路由

- [x] 2.1 新建 `apps/ai_assistant/views_tool_debug_drf.py`：`GET /api/ai/platform-tools/<name>`、`POST .../invoke`；写工具非超管 403；未知 404；`ValueError` → 400。验证：在 `tests/graybox/unit/test_ai_platform_tool_debug.py` 用 Django 测试客户端覆盖只读非超管 200、写非超管 403 且 handler 未被调用、未知 404（写法对齐 `test_device_prompts.py`）
- [x] 2.2 在 `urls.py` 注册上述路径（须排在 `platform-tools/toggle` 旁，且 **不得** 落在 `/api/ai/tools/` 前缀）。验证：`python manage.py check` 通过；路由名可 reverse；文档路径与代码一致

## 3. 前端调试页

- [x] 3.1 `api/toolbox.ts` 增加 fetch schema / invoke；`routes.ts` 增加 `/ai-assistant/toolbox/tools/:toolName`。验证：模块单测或类型检查覆盖 URL 拼接；前端检索无 `/api/ai/tools/` 调用
- [x] 3.2 新 L2 页（`WorkbenchHeader` + `WorkbenchCrumbs` 回工具箱）+ composable：按 schema 动态表单（无 `user_id`）；只读直接 invoke；写工具 `ElMessageBox.confirm`，取消不发请求；非超管写工具禁用执行；成功展示 JSON，`screenshot_page` 出图 + summary。验证：`frontend/tests/ai-assistant/p0/` 覆盖 confirm 取消不调用、非超管禁用执行、schema 字段不含 user_id
- [x] 3.3 `ToolboxPanel` 每张平台工具卡（含已停用）加「调试」跳转。验证：组件测或装配测断言停用卡仍有调试入口；浏览器走 `get_online_devices` 主路径看到返回数据

## 4. 文档与门禁

- [x] 4.1 更新 `dev_docs/DEV_TEST/接口文档/API-AI助手.md` 与 `frontend/src/modules/ai-assistant/AGENTS.md`（L2 调试路由、权限）。验证：文档路径/权限与 `urls.py` 一致
- [x] 4.2 关单：`python manage.py check`、相关 ruff、本变更 pytest、前端相关 vitest、`python tools/gen_arch_stats.py --check-boundaries`。验证：上述命令通过
