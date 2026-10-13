## Purpose

让执行角色在运行时只把当前步骤需要的设备工具和执行技能交给模型，截图与返回键保持始终可用，其余按组打开或关闭。

## ADDED Requirements

### Requirement: 常驻组始终暴露截图与返回键
执行角色的常驻组 MUST 始终处于激活状态，且只包含 `screenshot_page` 与 `press_key`。组开关 MUST NOT 关闭这两个工具，也 MUST NOT 把其他设备工具放进常驻组。任意一次组开关之后，模型可见工具 MUST 仍包含这两个工具。

#### Scenario: 尚未打开任何可开关组
- **WHEN** 按当前执行角色配置组装工具包，且没有打开任何可开关组
- **THEN** 模型可见工具包含 `screenshot_page`、`press_key` 和组开关，且不包含 `click_ratio`、`tap_screen`、`swipe_screen`、`drag_ratio`、`xpath_action`、`input_text`、`app_control`

#### Scenario: 打开其他组后常驻工具仍在
- **WHEN** 组开关只打开「点击滑动」组
- **THEN** 模型可见工具仍包含 `screenshot_page` 与 `press_key`

### Requirement: 设备动作分成四个可开关组
`click_ratio`、`tap_screen`、`swipe_screen`、`drag_ratio` MUST 同属「点击滑动」组，组标识为 `gesture`。`xpath_action` MUST 单独属于「xpath」组，组标识为 `xpath`。`input_text` MUST 单独属于「输入」组，组标识为 `text_input`。`app_control` MUST 单独属于「启停应用」组，组标识为 `app`。每个工具 MUST 只出现在一个组。各组说明 MUST 分别标明「点击滑动」「xpath」「输入」「启停应用」，供模型在开关前判断是否打开。

#### Scenario: 只打开点击滑动
- **WHEN** 组开关只把 `gesture` 设为打开
- **THEN** 非常驻的模型可见工具只有 `click_ratio`、`tap_screen`、`swipe_screen`、`drag_ratio`

#### Scenario: 只打开 xpath
- **WHEN** 组开关只把 `xpath` 设为打开
- **THEN** 非常驻的模型可见工具只有 `xpath_action`

#### Scenario: 只打开输入
- **WHEN** 组开关只把 `text_input` 设为打开
- **THEN** 非常驻的模型可见工具只有 `input_text`

#### Scenario: 只打开启停应用
- **WHEN** 组开关只把 `app` 设为打开
- **THEN** 非常驻的模型可见工具只有 `app_control`

### Requirement: 组开关写入最终状态
一次组开关 MUST 覆盖全部可开关组的激活状态。本次未明确设为打开的可开关组 MUST 被关闭。常驻组 MUST 保持激活。开关结果 MUST 列出当前打开的可开关组；本次被打开且带有使用说明的组，MUST 把该说明放进开关结果。

#### Scenario: 第二次开关关掉先前打开的组
- **WHEN** 先只打开 `gesture`，再只打开 `text_input`
- **THEN** 非常驻的模型可见工具只剩 `input_text`，`gesture` 组内工具不再可见

#### Scenario: 明确关闭全部可开关组
- **WHEN** 组开关把每个可开关组都设为关闭
- **THEN** 模型可见工具只剩 `screenshot_page`、`press_key` 和组开关

### Requirement: 开始回复前只激活常驻组
执行角色开始回复前，可开关组 MUST 全部处于关闭状态。存在至少一个可开关组时，组开关 MUST 对模型可见。

#### Scenario: 首轮尚未开关
- **WHEN** 执行角色尚未调用组开关
- **THEN** 模型输入包含组开关、`screenshot_page` 与 `press_key`，不包含四个动作组中的工具，也不包含「平台业务工具」组中的技能名称

### Requirement: 平台业务工具组与工具组同一次开关
当前执行技能目录 MUST 归入「平台业务工具」组，组标识为 `platform_business`，组说明 MUST 标明「平台业务工具」。该目录 MUST NOT 出现在常驻组。该组关闭时，其中技能的名称与说明 MUST NOT 进入模型输入。该组打开时，模型输入 MUST 列出这些技能的名称与描述，并要求先读取技能全文。打开或关闭该组 MUST 与设备工具组使用同一次组开关。

#### Scenario: 关闭时技能不可见
- **WHEN** `platform_business` 关闭
- **THEN** 模型输入不包含技能 `platform-tools-manual` 的名称

#### Scenario: 与点击滑动同时打开
- **WHEN** 同一次组开关打开 `platform_business` 和 `gesture`，其余可开关组关闭
- **THEN** 模型可见 `gesture` 组的工具，并列出 `platform-tools-manual`；`xpath_action`、`input_text`、`app_control` 仍不可见

### Requirement: 未归组或未知名字不能组装
执行角色启用的每个工具 MUST 归入恰好一个组。配置引用未知工具名，或把同一个工具名放进两个组时，组装 MUST 失败，且错误信息包含该名字。当前技能名单中的执行技能目录 MUST 归入 `platform_business`。

#### Scenario: 未知工具名
- **WHEN** 配置引用一个不存在的工具名
- **THEN** 组装失败，错误信息包含该名字

#### Scenario: 同一工具进入两组
- **WHEN** 同一工具名同时列入 `gesture` 和 `xpath`
- **THEN** 组装失败，错误信息包含该名字
