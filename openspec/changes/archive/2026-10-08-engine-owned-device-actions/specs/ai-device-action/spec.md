## MODIFIED Requirements

### Requirement: 智能体可执行设备 UI 动作

系统 SHALL 使 AI 智能体可对指定设备执行 `start_app / stop_app / click / long_click / swipe / back / input_text` 之一，并 SHALL 保留只读的 `current`（不产生设备副作用，仅读取前台应用）。`click`/`long_click` MUST 使用设备像素坐标，`swipe` MUST 使用方向与距离，`back` MUST 触发系统返回键。这些写动作 SHALL 由引擎侧设备工具经系统中转层直接执行；平台侧同名工具在本变更中 SHALL 保持现状不变（继续服务外部工具通道与工具箱调试页），引擎装配时 MUST 跳过注入清单里的同名设备动作工具，使同一动作在模型可见的工具集里只有一份。工具名、入参、返回形状与前端可见行为 MUST NOT 变化。

#### Scenario: 启动被测 App

- **WHEN** 智能体对指定设备调用 `start_app` 并传入包名
- **THEN** 该 App 在该设备上被启动并进入前台

#### Scenario: 点击页面元素坐标

- **WHEN** 智能体对指定设备调用 `click` 并传入元素中心坐标
- **THEN** 设备在对应坐标执行点击

#### Scenario: 读取当前前台

- **WHEN** 智能体对指定设备调用 `current`
- **THEN** 返回该设备当前前台 `package` 与 `activity`，且不改变设备状态

#### Scenario: 写动作由引擎工具执行

- **WHEN** 引擎在没有平台注入实现的情况下执行任一写动作
- **THEN** 动作经系统中转层直接作用于目标设备，且模型可见的设备动作只有引擎自带的一份

## ADDED Requirements

### Requirement: 设备工具带登记清单

引擎 SHALL 以一份登记清单描述设备动作工具：每项含名字、说明书（描述与参数表）、实现引用与元数据（是否只读、是否串行、是否设备动作）。该清单 MUST 为纯数据且不依赖任何 AI 框架，框架翻译发生在清单之外的单独一层。

#### Scenario: 登记清单是唯一真相源

- **WHEN** 引擎装配设备工具
- **THEN** 装配只依据登记清单的名字、说明书与实现引用，不在别处再写一份描述

#### Scenario: 清单不依赖框架

- **WHEN** 检查登记清单模块的依赖
- **THEN** 它只含纯数据与实现引用，不 import 任何 AI 框架

### Requirement: 平台侧设备工具在本变更中保持不变

平台侧既有的设备动作工具 SHALL 在本变更中保持现状：其实现、入参、返回形状、分类元数据与启停开关行为 MUST NOT 变化；引擎侧设备工具 MUST NOT 改变平台工具的调用结果。

#### Scenario: 平台工具行为不变

- **WHEN** 经外部工具通道或工具箱调试页调用平台侧设备工具
- **THEN** 其行为与本次变更前一致

#### Scenario: apps 目录零改动

- **WHEN** 审阅本变更的改动范围
- **THEN** `apps/` 下没有任何文件改动
