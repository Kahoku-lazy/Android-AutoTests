## Why

智能体「看屏幕」只有截图这一条通道，而这条通道上三处口径目前互相打架：工具实现（纯 adb 取帧、不落盘、只回图片）与四份规格（要求模型照抄「截图相对路径」）完全相反；执行角色提示词又要求模型用一个从未装配给任何角色的 `ocr_page` 工具。于是模型会照着提示词找不存在的工具、照着规格抄一个永远拿不到的路径，而截图本身还要为一次 uiautomator2 连接付费——u2 服务不可用时纯 adb 截图也跟着失败。

## What Changes

- **提示词对齐现行规格**：执行角色提示词删掉「用 OCR 工具重新识别定位」的表述（现行 `ai-screen-vision` 已规定 OCR 工具 MUST NOT 装配给角色），定位口径收敛为「视觉归一化坐标 → xpath」两级；OCR 对模型完全不可见，也不再被引导去调用。
- **规格以代码为准**：截图工具的既定契约是「不落盘、不返回路径、参数只有 `serial`」，因此模型无从取得截图路径。四份规格里 `screenshot` 字段的取值来源改为「不采集、恒为空串」，任务详情页相应呈现按「该步无截图路径」如实标注。`click_timer` 等已无实现承载的其余条目本单不动，记为已知债务。
- **截图与 uiautomator2 解耦**：`AndroidControl` 的 u2 会话改为惰性建立——只有 `find_xpath` 与非 ASCII 输入才连 u2；截图、层级 dump、点击、长按、滑动、拖动、按键、应用启停全部只走 adb，不再受 u2 服务可用性影响，也不再付一次 u2 连接开销。

## 关联文档

无 PRD 需求编号：本次需求来自 2026-10-20 会话中对三项缺陷的确认（提示词与规格的 OCR 表述漂移、`screenshot` 字段规格与实现相反、截图被 uiautomator2 绑定），属缺陷修正而非新增业务需求。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ai-device-action`: 新增「截图取帧不依赖 uiautomator2」要求；现有「截图工具只编一次并只给出模型图」要求的其余口径不变。
- `ai-executor-output`: 执行模型 `screenshot` 字段的取值来源由「照抄点击后截图返回的路径」改为「截图工具不返回路径，该字段不采集、恒为空串」；任务详情页执行结果段与验收模型输入中该字段的呈现口径同步。
- `ai-verifier-output`: 验收模型 `screenshot` 字段的取值来源同上；任务详情页验收段的验证截图呈现口径同步。
- `ai-executor-log-check`: 点击证据里「点击后截图路径」的取证口径改为与截图工具一致（只记已截图 / 未截图，不产生路径），点击时间点部分不变。
- `ai-task-publishing`: 任务详情页与任务过程记录中「验证截图路径」的保留与呈现口径改为「按截图工具实际可提供的内容」，不要求路径。

## Impact

- 引擎驱动层：`engines/device/android/android_device.py` 的 `AndroidControl`（u2 连接惰性化）。
- 引擎工具/提示词层：`engines/agents/prompts/executor_prompt.py`（删 OCR 表述）；`engines/agents/tools/tool_device.py`、`tool_ocr.py`、`apps/device_inspector/service.py` 三个截图调用点无需改代码，但行为都随之不再连 u2。
- 规格：`openspec/specs/ai-device-action`、`ai-executor-output`、`ai-verifier-output`、`ai-executor-log-check`、`ai-task-publishing`。
- 不改业务接口与前端：`screenshot` 为空时前端已有「未截图如实标注」分支，存量记录仍按原字段展示。
- 测试范围：`tests/engines/devices/test_android_device.py`、`tests/engines/agents/test_tool_device.py`、`tests/engines/agents/test_ocr_tool.py`（不跑全量回归）。
