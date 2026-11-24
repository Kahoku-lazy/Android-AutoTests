# backend-bridge-sop Specification

## Purpose
给平台一条可触发、有验收结论的 UI SOP：执行者动手、验收者逐条核对，一次运行留一份报告与一份用量。编排全部复用 `engines/ae_harness` 的现成抽象，本层只做装配。

## Requirements

### Requirement: SOP 只装配不自创

平台 SOP MUST 复用 `engines/ae_harness/workflow/sop` 的 `load_spec` 与 `run_sop` 完成编排；MUST NOT 另写步骤推进、重试预算、驳回记录或验收判定。

步骤定义 MUST 由调用方以 YAML 提供给 `load_spec`；MUST NOT 新增第二份步骤格式，MUST NOT 把步骤写死在代码里，MUST NOT 由 `ae_harness` 自带步骤文件。

本变更 MUST NOT 修改 `engines/ae_harness` 下的任何代码。

#### Scenario: 复用现成编排

- **WHEN** 平台跑一次 SOP
- **THEN** 步骤推进与重试由 `run_sop` 完成
- **AND** 本层源码里没有第二套编排循环

#### Scenario: 步骤来自调用方

- **WHEN** 平台跑一次 SOP
- **THEN** 步骤来自调用方传入的 YAML
- **AND** `ae_harness` 内不存在自带的步骤文件

#### Scenario: ae_harness 零改动

- **WHEN** 审查本变更的改动范围
- **THEN** `engines/ae_harness/` 下没有代码改动

### Requirement: 两个角色按同一套规则装配

平台 SOP MUST 装配两个角色：执行者挂全量设备工具，验收者**只**挂只读工具；两者 MUST 经 `ae_harness.agents.create_agent` 创建，MUST 复用现有提示词。

两个角色 MUST 共用一个观测中间件，使观测记录能按角色名区分。

#### Scenario: 验收者无写权限

- **WHEN** 装配验收者
- **THEN** 它只带只读工具

#### Scenario: 两类角色的密钥各归各

- **WHEN** 两个角色使用不同密钥
- **THEN** 报告与用量按角色分别归属

### Requirement: 一次运行的返回值

平台 SOP MUST 提供「跑一次」的入口：接收任务文本与可选的流程标识，返回结构化结果。

结果 MUST 至少包含：最终阶段、每步的名称/是否通过/尝试次数/说明、报告路径、日志路径、token 四类合计、按密钥分组的调用次数、逐次用量。

入口 MUST NOT 打印、MUST NOT 读命令行参数、MUST NOT 进入交互循环。

#### Scenario: 拿到每步结论

- **WHEN** 一次 SOP 运行结束
- **THEN** 返回值含每一步的名称、是否通过、尝试次数
- **AND** 含报告与日志路径

#### Scenario: 不打印

- **WHEN** 调用该入口
- **THEN** 不向标准输出写任何内容

### Requirement: 一次运行一套角色

每次运行 MUST 新建执行者与验收者；MUST NOT 跨运行复用上一轮的角色实例。

SOP 的运行彼此独立：后一次运行 MUST NOT 看到前一次运行的对话上下文。

#### Scenario: 两次运行互不影响

- **WHEN** 连续跑两次 SOP
- **THEN** 两次各自新建角色
- **AND** 第二次看不到第一次的上下文

### Requirement: 报告与用量落在平台目录

报告 MUST 输出到 `logs/agents/backend_bridge/`，每次运行一个独立时间戳子目录，文件名带 SOP 角色名。

token 用量 MUST 整理成结构化数据交回调用方，由后端写入既有账本；本层 MUST NOT 直接写库。

#### Scenario: 报告与单角色同根

- **WHEN** 一次 SOP 运行结束
- **THEN** 报告位于 `logs/agents/backend_bridge/<时间戳>/` 下
- **AND** 文件名带 SOP 角色名

### Requirement: 平台侧有触发入口

平台 MUST 提供一个可执行的一次性触发入口，把「跑一次 → 出报告 → 入账」串起来，使本变更在没有对话入口时仍可端到端验证。

该入口 MUST 与单角色命令并列，MUST NOT 经对话页或对话接口触发。

#### Scenario: 命令跑通全链路

- **WHEN** 执行该入口并给一条任务
- **THEN** 报告落在平台报告目录
- **AND** 用量写入账本
- **AND** 输出每步的通过情况

### Requirement: 对话页不参与

本变更 MUST NOT 改动 AI 助手对话页的任何行为：对话清单 MUST 仍只有单角色卡，SOP MUST NOT 出现在对话模块。

#### Scenario: 对话清单不变

- **WHEN** 请求对话卡片清单
- **THEN** 结果与变更前一致
- **AND** 不含 SOP 卡片
