# ai-device-action Specification

## Purpose
TBD - created by archiving change add-ai-device-action. Update Purpose after archive.
## Requirements
### Requirement: 智能体可执行设备 UI 动作

系统 SHALL 提供一个平台写工具，使 AI 智能体可对指定设备执行 `start_app / stop_app / click / long_click / swipe / back / input_text / current` 之一；`click`/`long_click` MUST 使用设备像素坐标，`swipe` MUST 使用方向与距离，`back` MUST 触发系统返回键，`current` MUST 不产生设备副作用、仅读取前台应用。

#### Scenario: 启动被测 App

- **WHEN** 智能体对指定设备调用 `start_app` 并传入包名
- **THEN** 该 App 在该设备上被启动并进入前台

#### Scenario: 点击页面元素坐标

- **WHEN** 智能体对指定设备调用 `click` 并传入元素中心坐标
- **THEN** 设备在对应坐标执行点击

#### Scenario: 读取当前前台

- **WHEN** 智能体对指定设备调用 `current`
- **THEN** 返回该设备当前前台 `package` 与 `activity`，且不改变设备状态

### Requirement: 设备动作受可用性与占用约束

系统 SHALL 在执行任何设备动作前校验目标设备已注册；当设备被执行引擎占用时 SHALL 拒绝执行并返回错误，且不产生设备副作用。

#### Scenario: 设备未注册

- **WHEN** 智能体对未注册的 serial 调用设备动作
- **THEN** 返回"设备未注册"错误，不执行动作

#### Scenario: 设备被执行引擎占用

- **WHEN** 目标设备处于执行引擎占用（占用标识含执行前缀）
- **THEN** 返回"设备正被执行引擎占用"错误，不执行动作

### Requirement: 动作返回前台应用供跳转判定

系统 SHALL 在每次动作执行后返回目标设备当前前台 `package` 与 `activity`，使智能体能据此判断点击是否引发页面跳转。

#### Scenario: 点击后前台变化

- **WHEN** 智能体点击一个可跳转元素后读取返回的前台
- **THEN** 返回的前台 `package`/`activity` 与点击前不同，智能体据此判定发生了跳转

### Requirement: 智能体可发现设备已安装的 App 包名

系统 SHALL 提供一个只读平台工具，使 AI 智能体可按关键词查询设备已安装包名，以自主获取被测 App 包名后再启动该 App。

#### Scenario: 按关键词获取包名

- **WHEN** 智能体对指定设备调用包名查询并传入关键词（如 `govee`）
- **THEN** 返回该设备已安装包名中包含该关键词的包名列表（如 `com.govee.home`）

