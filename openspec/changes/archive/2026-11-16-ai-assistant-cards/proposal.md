## Why

`/ai-assistant` 现在是占位页。运营侧已有 Agent 配置（名称、模型、系统提示词），但用户无法把它做成可对话的助手，也无法勾选 Harness 工具。助手要能入库、能测试对话，并留下一张 SOP 以后可读取的当前配置；SOP 本身本期不做。

## What Changes

- 新增助手名片：用户自定义显示名与头像，并引用一条运营 Agent 配置。卡片只显示这三样。
- 助手写入新表 `ai_assistants`。编号为创建当日 `YYYYMMDD` + `_` + 3 位大写字母或数字，唯一且创建后不变。与运营 `role_id`（无下划线、小写）分开。
- 头像只作展示。服务端压到最长边 128 像素的 JPEG 后再以 base64 入库，单张不超过 12KB。列表不下发头像正文，按编号单独取。
- 未上传头像时，卡片中间圆用该助手的笔色做深到浅。笔色在创建时从自定义色板按编号顺序分配，只保证相邻编号不同色，不按彩虹序。换头像不换色。
- 工具从 `engines/ae_harness/tools/` 的只读目录勾选：域、预设（全部 / 只读）、可选的单个函数例外。保存名字，不保存函数。挂载仍走域门面。
- 点「对话」不跑模型。每个对话栏首次发送才按当时名片造一个 Agent，本栏之后复用同一实例，上下文连续。多栏互不串。
- 刷新或离开页面不取消进行中的轮次；只有该栏的「取消」才停。服务重启后进行中的轮次标为已中断，不续跑。
- 改名片不影响已打开对话栏里的实例。新对话栏与以后的 SOP 都读名片的当前配置。本期不实现 SOP。
- 助手颜料片与对话页笔色登记为 AI 助手专有风格。笔色渐变用于无头像圆、发送钮和对话页头图标。当前对话栏用浅蓝填充加墨色框。虚线只允许颜料片与对话栏面板。不改全站 Doodle Craft。
- **BREAKING**（展示）：`/ai-assistant` 从占位页改为助手卡片与对话页。不改 `/api/ai/roles/`，不改任务清单引用的 `api/agents.ts`。

## 关联文档

无。`dev_docs/ARCH_PRD/PRD-平台总需求.md` 不覆盖「用户助手名片 + 测试对话」。本变更不改既有智能体列表不下发头像的口径；新头像走独立按编号接口。

## Capabilities

### New Capabilities

- `ai-assistant-card`: 助手名片的编号、显示名、压缩头像、笔色、对运营 Agent 配置的引用、工具勾选，以及卡片只显示三样信息。
- `ai-assistant-tool-catalog`: Harness 工具域的只读目录，以及按域 / 预设 / 函数例外保存与挂载。
- `ai-assistant-test-chat`: 多对话栏、发送才跑、同栏续聊、离开不取消、主动取消、重启中断。
- `ai-assistant-marker-style`: AI 助手专有颜料片与对话页笔色；虚线与渐变的允许范围。

### Modified Capabilities

（无。既有 `ai-assistant` 约束的是旧智能体列表接口，本变更不改那些路径与字段。）

## Impact

- 后端：`backend/apps/ai_assistant` 新增助手表、编号、头像压缩、工具目录与测试对话接口。写库走 `api.py`。
- 引擎：`engines/ae_harness/tools` 增加只读目录，不在工具里造 Agent。`engines/backend_bridge` 增加按名片装配与按对话栏续跑；不引用 `ae_harness/assistant/`。取消复用现有 `CancelToken`，登记键改为对话栏，不复用任务号表。
- 前端：`frontend/src/modules/ai-assistant` 替换占位页；模块色板与 doodle-craft 登记专有风格。
- 测试：编号格式与唯一、头像体积、列表不含头像正文、同栏续聊、离开不取消、重启标中断。
- 不触碰：SOP 编辑与启动、运营 Agent 配置的字段、任务清单、钱与配额口径。
