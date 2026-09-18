## Purpose

让 AI 智能体按「model + Harness」组织为多套专用 Harness（意图识别 / 视觉 / 推理 / 强模型），一个对话经意图识别后路由到对应 Harness 执行，使繁杂任务各司其职、有条理完成。

## ADDED Requirements

### Requirement: 智能体由多套 Harness 组成

系统 SHALL 将一个智能体组织为多套 Harness（意图识别、视觉、推理、强模型），每套 Harness 独立绑定自己的模型、工具子集与提示词。

#### Scenario: 每套 Harness 独立配置

- **WHEN** 管理员配置一个智能体
- **THEN** 该智能体包含意图识别、视觉、推理、强模型四套 Harness，各自绑定独立模型与工具子集

### Requirement: 意图识别输出格式化结果

系统 SHALL 在对话开始时先用意图识别 Harness 理解用户意图，并输出格式化结果：`intent`（意图描述）、`intent_code`（1=视觉、2=推理）、`prompt`（模型优化后的精准任务描述）。

#### Scenario: 需要视觉的任务

- **WHEN** 用户输入"点击涂鸦"或"控制设备"这类需要看图的任务
- **THEN** 意图识别输出 `intent_code=1` 及一段优化后的任务提示词

#### Scenario: 只需推理的任务

- **WHEN** 用户输入"编写用例"或"测试某功能"这类纯文本任务
- **THEN** 意图识别输出 `intent_code=2` 及一段优化后的任务提示词

### Requirement: 按意图路由到对应 Harness 执行

系统 SHALL 按 `intent_code` 将对话路由到对应 Harness 执行：`1` 路由到视觉 Harness，`2` 路由到推理 Harness，并把优化后的 `prompt` 作为该 Harness 的输入。

#### Scenario: 视觉意图走视觉模型

- **WHEN** 意图识别输出 `intent_code=1`
- **THEN** 系统使用视觉 Harness（视觉模型 + 设备/截图工具）执行，并把优化后的 prompt 传入

#### Scenario: 推理意图走推理模型

- **WHEN** 意图识别输出 `intent_code=2`
- **THEN** 系统使用推理 Harness（推理模型 + 用例/执行工具）执行，并把优化后的 prompt 传入

### Requirement: 强模型手动短路开关

系统 SHALL 支持一个手动开关：当开启时，跳过 `intent_code` 的 1/2 选择，直接将对话下发给强模型 Harness 执行。

#### Scenario: 开关开启时短路

- **WHEN** 强模型开关为开启状态
- **THEN** 系统不论意图识别输出 1 还是 2，都直接路由到强模型 Harness 执行

#### Scenario: 开关关闭时正常选择

- **WHEN** 强模型开关为关闭状态
- **THEN** 系统按 `intent_code` 在视觉与推理 Harness 之间选择

### Requirement: 对话入口对用户透明

系统 SHALL 对用户只暴露一个对话入口，用户无需感知背后的多 Harness 编排与路由过程。

#### Scenario: 用户只对话

- **WHEN** 用户通过对话入口输入任意内容
- **THEN** 系统自动完成意图识别、路由与执行，用户仅看到最终回复
