## Why

平台工具调试页的入参目前全部是自由输入框。设备管理分类下真正操作手机的工具（`list_apps`、`device_action`、`click_ratio`、`drag_ratio`、`xpath_action`）都必须先填 `serial`，而 serial 是设备池里的已知值。手输一旦拼错，轻则工具报「设备未注册」，重则选到使用中或被执行引擎占用的设备，白跑一趟。需要让这几个工具的设备参数从平台已连接、在线且未被占用的设备中选择。

## What Changes

- 设备管理分类下 **5 个真正操作手机的工具**（`list_apps`、`device_action`、`click_ratio`、`drag_ratio`、`xpath_action`）的 `serial` 参数，由自由输入框改为**可选择平台设备的下拉**。
- 候选范围：**对请求者可见 + 已连接在线 + 未被占用**（不含使用中、不含被执行引擎占用的设备），可见性口径与设备管理列表一致。
- 候选随调试 schema 一并返回，**不新增接口**；无可选值的参数 schema 与现状逐字段一致。
- 下拉**保留手输兜底**：目标设备不在清单时仍可填写并提交；候选为空给可读提示且 MUST NOT 阻塞执行。
- **不改** `acquire_device` / `release_device`：二者是设备池占用记账、不操作手机，保持自由输入。
- **非目标**：设备检查器 / 视觉识别 / 工作流分类的工具参数；静态枚举（动作类型、方向、释放原因）；`package` 等级联候选；工具运行时装配与「交给助手」启停语义。

## 关联文档

- PRD-00（需求总纲，AI 工具箱增量）
- 前置变更：`add-platform-tool-debug`（调试页与 JWT invoke 链路）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-platform-tool-debug`: 「调试页按 schema 收集入参并展示结果」增加「候选值由服务端给出时渲染为可选择控件且保留手输」；「登录用户可读取工具入参 schema」扩展为携带已按可见性收窄的设备候选清单；新增「设备参数候选限于可见、在线且未被占用的设备」。

## Impact

- 后端：`apps/ai_assistant/tools.py`（候选登记表 + schema 候选声明）、`apps/ai_assistant/views_tool_debug_drf.py`（用请求者身份解析候选）；只读调用 `apps/device_pool/api.py::list_devices`（不改其实现）
- 前端：`frontend/src/modules/ai-assistant/api/toolbox.ts`（参数字段扩展）、`composables/useToolDebug.ts`、`ToolDebugPage.vue`（下拉控件）、模块 `AGENTS.md` 增量
- 测试：`tests/graybox/unit/test_ai_platform_tool_debug.py`（候选登记、可见性收窄）、`frontend/tests/ai-assistant/p0/useToolDebug.spec.ts`
- 文档：AI 助手接口文档登记 schema 新增字段与候选口径
- 引擎 / 数据库迁移 / 内部令牌网关：无
