## MODIFIED Requirements

### Requirement: 常驻组始终暴露截图与返回键
执行角色的常驻组 MUST 始终处于激活状态，且只包含 `screenshot_page`、`mark_dot` 与 `press_key`。组开关 MUST NOT 关闭这三个工具，也 MUST NOT 把其他设备工具放进常驻组。任意一次组开关之后，模型可见工具 MUST 仍包含这三个工具。

#### Scenario: 尚未打开任何可开关组
- **WHEN** 按当前执行角色配置组装工具包，且没有打开任何可开关组
- **THEN** 模型可见工具包含 `screenshot_page`、`mark_dot`、`press_key` 和组开关，且不包含 `click_ratio`、`tap_screen`、`swipe_screen`、`drag_ratio`、`xpath_action`、`input_text`、`app_control`

#### Scenario: 打开其他组后常驻工具仍在
- **WHEN** 组开关只打开「点击滑动」组
- **THEN** 模型可见工具仍包含 `screenshot_page`、`mark_dot` 与 `press_key`

### Requirement: 组开关写入最终状态
一次组开关 MUST 覆盖全部可开关组的激活状态。本次未明确设为打开的可开关组 MUST 被关闭。常驻组 MUST 保持激活。开关结果 MUST 列出当前打开的可开关组；本次被打开且带有使用说明的组，MUST 把该说明放进开关结果。

#### Scenario: 第二次开关关掉先前打开的组
- **WHEN** 先只打开 `gesture`，再只打开 `text_input`
- **THEN** 非常驻的模型可见工具只剩 `input_text`，`gesture` 组内工具不再可见

#### Scenario: 明确关闭全部可开关组
- **WHEN** 组开关把每个可开关组都设为关闭
- **THEN** 模型可见工具只剩 `screenshot_page`、`mark_dot`、`press_key` 和组开关

### Requirement: 开始回复前只激活常驻组
执行角色开始回复前，可开关组 MUST 全部处于关闭状态。存在至少一个可开关组时，组开关 MUST 对模型可见。

#### Scenario: 首轮尚未开关
- **WHEN** 执行角色尚未调用组开关
- **THEN** 模型输入包含组开关、`screenshot_page`、`mark_dot` 与 `press_key`，不包含四个动作组中的工具，也不包含「平台业务工具」组中的技能名称
