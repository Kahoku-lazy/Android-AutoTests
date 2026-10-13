## Why

执行模型的工具子集今天同时含引擎自带设备动作工具与 6 个平台注入工具（设备台账、设备信息、日志查询）。既然设备动作已归引擎，执行链路的工具面要收敛成一份：执行模型只保留引擎自带的 9 个设备动作工具，平台侧那 6 个工具不再进入模型工具子集（工具与实现原样保留，仅供工具网关、工具箱调试页与其它链路使用）。

## What Changes

- `VISION_TOOLS`（执行模型工具子集）收敛为引擎自带的 9 个设备动作工具：`screenshot_page` / `click_ratio` / `tap_screen` / `xpath_action` / `swipe_screen` / `drag_ratio` / `input_text` / `press_key` / `app_control`。**只改这一个字段**。
- 从执行模型工具子集中移除的 6 个：`list_devices` / `acquire_device` / `release_device` / `current_app` / `list_apps` / `read_device_log`（平台侧实现、分类元数据、启停开关与工具调试入口全部保持现状）。
- 规格同步：设备日志查询工具的装配要求由「装配进执行模型」改为「不装配进任何模型角色」；包名查询工具明确为平台侧只读工具、不再装配进执行模型。
- 提示词同步：执行提示词里的「平台设备操作 SOP」段删除（该段写死了操作顺序，并引用执行模型已不再装配的 `list_devices`）；「行为规范」与「截图铁律」保留。
- 测试同步：四处断言旧工具子集的既有用例改为断言新子集。
- 非目标（不动）：规划模型与验收模型的工具子集；平台侧 6 个工具的实现与界面；设备动作工具的归属（仍归引擎）；平台调试台的既有排除规则（设备池记账工具不进调试对话）。

## 关联文档

- `PRD-08-AI助手`（需求总纲登记的 AI 助手模块）
- `ARCH-00-平台总体架构`（§1.1 分层口径 L1c 引擎层）

## Capabilities

### New Capabilities

（无新增能力。）

### Modified Capabilities

- `device-log-read-tool`: 「工具装配进执行模型」这条要求被替换——通用日志查询工具不再装配进任何模型角色，仅经工具网关与工具箱调试页调用；验收模型继续用按关键词规则检查的只读工具。同时新增一条要求把「日志排查由平台侧承担」的口径写清。
- `ai-device-action`: 「智能体可发现设备已安装的 App 包名」明确为平台侧只读工具，不再装配进执行模型。

## Impact

- **引擎**：`engines/ai/agents/config.py` 的 `VISION_TOOLS` 一个字段。
- **规格**：`device-log-read-tool` 与 `ai-device-action` 两份 delta。
- **测试**：`tests/graybox/unit/test_device_log_read_tool.py`、`tests/graybox/unit/test_ai_model_debug.py` 中共三处断言需同步。
- **行为变化（已确认接受）**：执行模型不再能查设备日志、发现设备列表、查已安装包名、读当前前台、锁定/释放设备。其中「动作后返回当前前台」不受影响（由动作工具自带返回）；设备 serial 仍由任务输入前缀给出。
- **不变**：`apps/` 无改动；前端无改动；平台侧 6 个工具仍可从工具网关与工具箱调试页调用。
