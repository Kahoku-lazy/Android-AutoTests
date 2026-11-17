## Purpose

给只有一个智能体的工作流单独的编排目录。第一张是 Android UI 控制，复用现有 UI 执行角色，不走双角色 SOP。

## ADDED Requirements

### Requirement: 单智能体编排与 SOP 分开存放

单智能体编排 MUST 放在 workflow 下的独立目录。该目录 MUST NOT 创建第二个角色，MUST NOT 调用 SOP 引擎。现有设备 SOP 与用例编写流水线 MUST 保持原路径与原行为。

#### Scenario: 目录只服务一个智能体

- **WHEN** 查看单智能体编排目录
- **THEN** 其中的运行入口只装配并调用一个智能体
- **AND** 设备 SOP 文件没有被改成单智能体

### Requirement: Android UI 控制复用执行角色

系统 SHALL 提供名为「Android UI 控制」的单智能体编排。它 MUST 使用现有 UI 执行角色的提示词、模型与 device/observe 工具，MUST NOT 再定义一套点击工具或提示词。

#### Scenario: 只建一个执行者

- **WHEN** 启动 Android UI 控制
- **THEN** 运行中只存在一个 UI 执行智能体
- **AND** 不存在验收智能体，也不创建 SOP 步骤

### Requirement: 编排清单可被页面读取

系统 SHALL 提供单智能体编排清单。本期清单 MUST 至少包含「Android UI 控制」，并给出稳定键、显示名和一句说明。未知键 MUST 拒绝运行。

#### Scenario: 清单含 Android UI 控制

- **WHEN** 页面请求编排清单
- **THEN** 结果包含键 `android_ui`、显示名「Android UI 控制」
- **AND** 请求不存在的键时返回可读错误
