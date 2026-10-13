## ADDED Requirements

### Requirement: 引擎以框架步骤承载执行与验收

引擎 SHALL 使用 AgentScope 的标准作业流程（SOP）承载「执行 + 验收」的步骤化编排，MUST NOT 再自建执行 ↔ 验收的重试循环。引擎对 AgentScope 的依赖版本 SHALL 满足该模块存在；升级依赖 MUST NOT 改变引擎零平台依赖的边界。

#### Scenario: 依赖面满足步骤编排

- **WHEN** 引擎按当前依赖版本装配并运行一次任务
- **THEN** 所用 AgentScope 版本提供 SOP 模块，且引擎既有的模型 / 凭证 / 消息块 / 事件流导入面不受影响

#### Scenario: 引擎仍零平台依赖

- **WHEN** 检查引擎源码的 import
- **THEN** 引擎 MUST NOT import 平台模块；运行状态与过程日志的落点仍由调用方注入

#### Scenario: 编排职责不再重复实现

- **WHEN** 检查引擎的步骤推进实现
- **THEN** 步骤推进、驳回计数与状态由框架步骤承载，引擎侧 MUST NOT 再保留同职责的自建循环
