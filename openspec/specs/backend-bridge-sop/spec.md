# backend-bridge-sop Specification

## Purpose
给平台一条可触发、有验收结论的 UI SOP：执行者动手、验收者逐条核对，一次运行留一份报告与一份用量。编排全部复用 `engines/ae_harness` 的现成抽象，本层只做装配。

## Requirements

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

### Requirement: 运行中异常中断也产出报告

一次 SOP 运行在事件记录器建立之后、正常结束之前抛出异常时，若该异常不是用户取消、也不是预算超限这类运行中断，本层 MUST 为这次运行补齐收尾并渲染一份 HTML 报告。报告 MUST 包含中断前已经产生的回复与观测事件，MUST 在概览里以可读文案标注「运行中断」与中断原因，MUST NOT 把这次运行呈现为全部步骤通过。

报告定位 MUST 通过失败回调交回调用方。回调 MUST 在报告落盘之后、原异常重新抛出之前调用，MUST 只接收一次；原异常 MUST 保持类型不变地抛出，MUST NOT 被替换成新的异常类型。

用户取消与运行中断（含预算超限）MUST NOT 产出报告；事件记录器尚未建立就失败（设备校验、角色装配、YAML 读取等）时 MUST NOT 产出报告。

#### Scenario: 模型调用异常中断后仍有报告

- **WHEN** 一次已开始执行、已产生事件记录的 SOP 运行因模型返回 400 抛出异常
- **THEN** 该次运行目录出现一份 HTML 报告，概览标注「运行中断」与中断原因
- **AND** 失败回调收到该报告定位，原异常继续向上抛出

#### Scenario: 报告含中断前的事件

- **WHEN** 运行在第二步执行期间中断，中断前已产生两轮回复与若干工具调用
- **THEN** 报告里能读到这两轮回复与工具调用记录
- **AND** 报告不出现「每一步都通过了」这类正常收尾文案

#### Scenario: 取消与运行中断不产报告

- **WHEN** 运行因用户关闭（取消异常）或预算超限中断
- **THEN** 该次运行目录不新增 HTML 报告
- **AND** 失败回调不被调用

#### Scenario: 起跑前失败不产报告

- **WHEN** 设备离线导致运行在建立事件记录器之前就失败
- **THEN** 不产出报告，失败回调不被调用
