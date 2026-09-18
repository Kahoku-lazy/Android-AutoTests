## 1. device_pool：设备动作入口

- [x] 1.1 在 `apps/device_pool/pool.py` 的 `DevicePool` 补三个公开包装方法 `action_start_app(pkg)` / `action_stop_app(pkg)` / `action_press_key(key="back")`，内部委托 `self._session()` 的对应原语。验证：`python manage.py check && ruff check apps/device_pool/pool.py`
- [x] 1.2 在 `apps/device_pool/api.py` 新增模块级 `_EXECUTION_OCCUPY_PREFIXES` 守卫、`use_device(serial)`（Device 存在校验 + 执行引擎占用拦截 + `device.switch_to`）与 `device_action(serial, action, ...)`（动作分发：start_app/stop_app/click/long_click/swipe/back/input_text/current，统一返回 `device.app_current()`），并将两者加入 `__all__`。验证：`ruff check apps/device_pool/api.py && python manage.py check`
- [x] 1.3 在 `apps/device_pool/pool.py` 补 `action_shell(cmd)` 包装、`apps/device_pool/api.py` 新增 `list_apps(serial, query="")`（`pm list packages` 解析 + 子串过滤，供 AI 自主获取被测 App 包名）并加入 `__all__`。验证：`ruff check apps/device_pool && pytest tests/device_pool/test_device_action.py -k list_apps`

## 2. ai_assistant：平台工具

- [x] 2.1 在 `apps/ai_assistant/agent_scope/tool_registry.py` 的 `TOOL_SCHEMAS` 新增 `device_action` schema（设备管理分类、`devices/action`、read_only=False、参数 serial/action/package/x/y/direction/distance/text/clear_first），并注册 handler 调 `apps.device_pool.api.device_action`。验证：`python manage.py check && ruff check apps/ai_assistant/agent_scope/tool_registry.py`
- [x] 2.2 检查并同步工具网关 action 白名单（`apps/ai_assistant/views/tool_gateway.py` 及其中间件），确保 `devices/action` 可经工具网关分发。验证：`rg "devices|action|白名单|whitelist" apps/ai_assistant -n` 确认新 action 已登记
- [x] 2.3 在 `TOOL_SCHEMAS` 新增 `list_apps` schema（设备管理分类、`devices/list_apps`、read_only=True、参数 serial/query）并注册 handler 调 `apps.device_pool.api.list_apps`。验证：`ruff check apps/ai_assistant/agent_scope/tool_registry.py && pytest tests/ai_assistant/test_tools_devices.py -k list_apps`

## 3. 测试与门禁

- [x] 3.1 新增/补充单元测试：`use_device` 对"未注册/执行引擎占用"抛错；`device_action` 各 action 正确分发到 `device` 单例对应方法（mock `device`），并返回 `app_current()`。验证：`pytest tests/device_pool -k "device_action or use_device"`（路径按项目既有测试布局调整）
- [x] 3.2 跨模块边界合规：`python tools/gen_arch_stats.py --check-boundaries` 通过（0 违规，AI handler 只 import device_pool.api）
- [x] 3.3 全链路门禁：`python manage.py check && ruff check apps/device_pool apps/ai_assistant && pytest -m "unit or integration"` 通过
