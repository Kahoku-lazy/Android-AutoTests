## MODIFIED Requirements

### Requirement: 平台角色只经 ae_harness 原语装配

平台侧角色 MUST 经 `ae_harness.agents.create_agent` 创建，MUST NOT 直接构造 `Agent`，MUST NOT 导入 `ae_harness.assistant` 下的任何模块。

角色 MUST 由调用方传入三样东西：系统提示词正文、连接参数（`provider`、`api_key_env`、`model_name`、可选 `base_url`）、以及创建后挂上的工具。平台 MUST NOT 读取引擎内的提示词文件，MUST NOT 接受模型短名。

设备执行角色挂全量设备工具。验收角色 MUST 只挂勾选与只读目录的交集。

#### Scenario: 装配出的角色可用设备工具

- **WHEN** 用一份运营配置构建平台设备执行角色
- **THEN** 返回的智能体带全量设备工具
- **AND** 其密钥环境变量名可从返回值读到

#### Scenario: 验收角色没有写操作

- **WHEN** 验收配置的勾选里含写操作工具
- **THEN** 写操作工具不在验收者的工具集里

#### Scenario: 不依赖控制台入口

- **WHEN** 审查本目录的导入
- **THEN** 不存在对 `ae_harness.assistant` 的导入
- **AND** 不存在对已删除的 `ae_harness.workflow.sop_runner` 的导入

### Requirement: 一次运行的入口契约

本目录 MUST 提供「跑一次任务」的入口。该入口 MUST 接收任务文本、系统提示词正文与连接参数，返回结构化结果，MUST NOT 打印、MUST NOT 读命令行参数、MUST NOT 进入交互循环，MUST NOT 接收模型短名。

返回结果 MUST 至少包含：最终文本、报告文件路径、日志文件路径、token 四类合计、按密钥环境变量名分组的调用次数、逐次用量明细。

入口 MUST 在运行期间挂观测中间件，使压缩决策与最终提示词随产物落盘。

#### Scenario: 跑完拿到结构化结果

- **WHEN** 调用一次运行入口并正常结束
- **THEN** 返回值含最终文本与报告路径
- **AND** 含 token 四类合计与按密钥分组

#### Scenario: 结果不依赖打印

- **WHEN** 入口正常结束或失败
- **THEN** 标准输出没有本次运行的结果文本

### Requirement: 控制台入口零影响

平台装配 MUST NOT 调用 `ae_harness.assistant` 或已删除的控制台 SOP 入口。控制台单智能体与 SOP 调试入口已删除，本需求不再要求它们继续可运行。

#### Scenario: 控制台入口行为不变

- **WHEN** 审查 `backend_bridge` 的导入
- **THEN** 不存在 `agent_executor`、`agent_verifier` 或 `sop_runner` 的导入
