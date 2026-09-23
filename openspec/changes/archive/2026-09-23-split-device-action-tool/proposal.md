## Why

`device_action` 用 8 个动作分支（start_app/stop_app/click/long_click/swipe/back/input_text/current）和 9 个可选参数挤在一个工具里：模型看不出「哪些参数属于哪个动作」，调试页把用不到的参数一并铺开，工具名也说明不了它能干什么。本次按动作语义拆成 6 个职责单一的工具。

## What Changes

- **删除** `device_action`，**新增 6 个工具**（设备管理分类 8 → 13，平台工具总数 12 → 17）：

| 新工具 | 签名 | 只读 | 承接原动作 |
|---|---|---|---|
| `app_control` | `(serial, action, package="")`，action ∈ start_app/stop_app | ❌ 写 | start_app、stop_app |
| `tap_screen` | `(serial, mode="click", x=0, y=0)`，mode ∈ click/long_click | ❌ 写 | click、long_click |
| `swipe_screen` | `(serial, direction="up", distance=500)` | ❌ 写 | swipe |
| `press_key` | `(serial)` | ❌ 写 | back |
| `input_text` | `(serial, text, clear_first=True)` | ❌ 写 | input_text |
| `current_app` | `(serial)` | ✅ **只读** | current |

- `current_app` 只读：它不动设备（只读当前前台），因此从原来的写工具里分出来，改为 `read_only=True`——免 HITL 确认、调试页任意登录用户可执行。
- `press_key` 仅按 BACK（等价迁移，不新增按键能力）。
- 5 个写工具进入 `AUTO_ALLOW_TOOLS`（承接原 `device_action` 的自动放行位）。
- **按性质重组工具箱分类（4 类 → 6 类）**：分类是**整类启停的单位**（每个分类有「全部启用/全部关闭」），原先把 13 个工具挤在「设备管理」一桶里，导致「一键停掉所有会改手机状态的控制工具」做不到。重组为：设备管理（台账 3）/ 设备控制（会在手机上产生副作用的 8 个）/ 设备信息（只读连设备 2）/ 设备检查器（1）/ 视觉识别工具（1）/ 工作流（2）。
- 同步：引擎 `VISION_TOOLS`、模型手册、主 spec 场景、接口文档、前端常量与模块 AGENTS.md、前后端测试。
- **DB 提示词再同步**：执行提示词有两处 `device_action(...)` 字面引用（swipe / input_text），沿用 0039 的**短语级条件替换**模式写新迁移。
- **BREAKING（工具面）**：`device_action` 不再是可调用工具（调用返回 404）。

## 关联文档

- PRD-00（需求总纲，AI 工具箱增量）
- 前置变更：`add-platform-tool-debug`、`remove-get-online-devices-tool`（同属工具面收敛）、`manage-device-assistant-prompts`（提示词种子来源）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-platform-tool-debug`: 「调试页按 schema 收集入参并展示结果」「登录用户可读取工具入参 schema」两处的场景样例工具由已删除工具改为 `tap_screen`；「设备参数候选限于可见、在线且未被占用的设备」的工具清单改为拆分后的需要 serial 的工具集合。

## Impact

- 后端：`apps/ai_assistant/tools.py`（删 1 个函数 + 新增 6 个、`TOOLS`/`TOOL_META`/`AUTO_ALLOW_TOOLS`/`DEBUG_PARAM_OPTIONS`）、新增数据迁移 `0040_*`、`0038` 种子文本
- 引擎：`engines/ai/agentscope/config.py`（`VISION_TOOLS`）
- 技能文档：`engines/ai/skills/platform-tools-manual/SKILL.md`
- 前端：`frontend/src/modules/ai-assistant/constants.ts`、模块 `AGENTS.md`
- 测试：`tests/graybox/unit/test_ai_platform_tool_debug.py`、`frontend/tests/ai-assistant/p0/useToolDebug.spec.ts`、`ToolDebugPage-device-options.spec.ts`
- 文档：AI 助手接口文档（schema 示例与候选工具口径）
- 数据库：无 schema 变更；一个可逆数据迁移（仅 `ai_agents` 自有表）
- **不动**：`click_ratio` / `drag_ratio` / `xpath_action`（它们本就是单一职责工具）、设备可见性规则、工具箱分类定义
