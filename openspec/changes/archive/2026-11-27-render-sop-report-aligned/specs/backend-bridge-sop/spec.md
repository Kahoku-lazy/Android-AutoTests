## MODIFIED Requirements

### Requirement: SOP 只装配不自创

平台 SOP MUST 复用 `engines/ae_harness/workflow/sop` 的 `load_spec` 与 `run_sop` 完成编排；MUST NOT 另写步骤推进、重试预算、驳回记录或验收判定。

步骤定义 MUST 由调用方以 YAML 提供给 `load_spec`；MUST NOT 新增第二份步骤格式，MUST NOT 把步骤写死在代码里，MUST NOT 由 `ae_harness` 自带步骤文件。

采集与渲染 MUST 复用 `engines/ae_harness` 的现有实现（对齐记录、原始事件流、报告渲染器）；本层 MUST NOT 自建第二套采集或渲染，MUST NOT 在 `ae_harness` 内另立编排抽象。

#### Scenario: 复用现成编排

- **WHEN** 平台跑一次 SOP
- **THEN** 步骤推进与重试由 `run_sop` 完成
- **AND** 本层源码里没有第二套编排循环

#### Scenario: 步骤来自调用方

- **WHEN** 平台跑一次 SOP
- **THEN** 步骤来自调用方传入的 YAML
- **AND** `ae_harness` 内不存在自带的步骤文件

#### Scenario: ae_harness 零改动

- **WHEN** 审查本变更新增的 SOP 侧代码
- **THEN** 没有任何新增的步骤推进、重试预算或验收判定
- **AND** `load_spec` 与 `run_sop` 仍是唯一编排入口

#### Scenario: 采集与渲染不自建

- **WHEN** 审查 SOP 运行产物的写入与渲染路径
- **THEN** 对齐记录、原始事件流与报告都来自 `ae_harness` 的现有实现
- **AND** 本层没有第二套事件折叠或 HTML 拼接代码

### Requirement: 报告与用量落在平台目录

一次 SOP 运行 MUST 产出四类文件，全部落在 `logs/agents/backend_bridge/` 下的同一时间戳子目录，文件名带 SOP 角色名：过程日志 `.jsonl`、对齐记录 `.aligned.json`、原始事件流 `.raw.jsonl`、报告 `.html`；媒体 MUST 落在与记录同名的 `.media` 目录。

报告 MUST 由对齐记录渲染，页签与视觉契约 MUST 与单角色报告一致（口径见 `ae-harness-sop-report`）。

token 用量 MUST 整理成结构化数据交回调用方，由后端写入既有账本；本层 MUST NOT 直接写库。

#### Scenario: 报告与单角色同根

- **WHEN** 一次 SOP 运行结束
- **THEN** 报告位于 `logs/agents/backend_bridge/<时间戳>/` 下
- **AND** 文件名带 SOP 角色名

#### Scenario: 四类文件同目录同前缀

- **WHEN** 一次 SOP 运行结束
- **THEN** 该次运行目录里同时存在过程日志、对齐记录、原始事件流与报告
- **AND** 四个文件名共用同一时间戳前缀与 SOP 角色名

#### Scenario: 报告由对齐记录渲染

- **WHEN** 打开本次 SOP 运行的报告
- **THEN** 页签与单角色报告一致
- **AND** 报告内容与对齐记录逐段对应

#### Scenario: 用量不直接写库

- **WHEN** 一次 SOP 运行结束
- **THEN** 用量以结构化数据返回调用方
- **AND** 本层代码里没有数据库写入

## ADDED Requirements

### Requirement: 设备由平台指定并前置校验

SOP 运行 MUST 由平台传入设备序列号；序列号为空时 MUST 拒绝运行并给出可读原因。

校验 MUST 在装配任何角色、发起任何模型调用之前完成：设备不存在、未连接或状态不是 `device` 时 MUST 拒绝运行，失败原因 MUST 含平台传入的序列号与当前在线设备清单。

运行全程 MUST 独占该设备：设备动作工具 MUST 拒绝平台未指定的其他序列号。

#### Scenario: 设备未连接时一步都不跑

- **WHEN** 平台传入一个未连接的序列号
- **THEN** 运行被拒绝，且未产生任何模型调用
- **AND** 失败原因里含该序列号

#### Scenario: 工具层拒绝换设备

- **WHEN** 运行中模型试图对另一个序列号执行设备动作
- **THEN** 工具返回拒绝
- **AND** 拒绝理由说明设备由平台指定

### Requirement: 观测采集与运行参数与单角色执行器对齐

SOP MUST 以采集全量上下文的方式装配观测：每轮模型真实收到的消息 MUST 入观测。

执行者与验收者 MUST 共用同一个观测中间件实例，记录按角色名区分；MUST NOT 为两个角色各建一个观测实例。

SOP 的运行参数 MUST 与单角色执行器取同一组值：保留图像数、工具结果上限、最大推理轮次；MUST NOT 依赖框架默认值。

#### Scenario: 两个角色共用一套观测

- **WHEN** 一次 SOP 运行结束
- **THEN** 观测里同时有执行者与验收者的记录
- **AND** 两个角色的记录都能追到各自的 reply_id

#### Scenario: 参数不取框架默认值

- **WHEN** 检查一次 SOP 运行的运行参数
- **THEN** 保留图像数、工具结果上限、最大推理轮次与单角色执行器相同
- **AND** 不出现框架默认的更大取值
