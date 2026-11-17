## Purpose

约定 `engines/agents` 整包退役后的边界：平台只有一条 Agent 落点（`engines/backend_bridge`）、只有一份原语（`engines/ae_harness`），引擎包之间不反向依赖，被下线的旁路能力不得以「临时兼容」名义复活，且退役状态可被机械校验。

## ADDED Requirements

### Requirement: 平台 Agent 只有一条落点

`engines/agents` MUST NOT 恢复为包。平台侧（后端任务、任务链、前端卡片）的角色装配、运行、事件落库与用量上送 MUST 只经 `engines/backend_bridge`；控制台调试入口 MUST 只在 `engines/ae_harness/assistant/`，且 `backend/apps/**` 与 `engines/backend_bridge/**` MUST NOT import 它。

#### Scenario: 旧包不再存在

- **WHEN** 检查 `engines/` 目录结构与全仓 import
- **THEN** 不存在 `engines/agents/` 目录，且仓内没有任何 `engines.agents` 形式的导入

#### Scenario: 平台新增角色只落在 backend_bridge

- **WHEN** 开发者新增一个平台可运行的智能体角色
- **THEN** 装配代码只出现在 `engines/backend_bridge/`，不新增第二个落点

#### Scenario: 平台不引用控制台入口

- **WHEN** 扫描 `backend/apps/**` 与 `engines/backend_bridge/**` 的 import
- **THEN** 不存在对 `engines.ae_harness.assistant` 的引用

### Requirement: 引擎包之间不反向依赖 Agent 落点

`engines/device`、`engines/vision`、`engines/uart_log` MUST NOT import 任何 Agent 相关包（含 `engines.backend_bridge`、`engines.ae_harness` 与其子包）。需要写过程日志时 SHALL 经共享出口 `utils.logs`。

#### Scenario: 设备引擎不依赖 Agent 包

- **WHEN** 扫描 `engines/device`、`engines/vision`、`engines/uart_log` 的 import
- **THEN** 三者都不出现 `engines.agents`、`engines.ae_harness`、`engines.backend_bridge`

#### Scenario: 设备侧日志经共享出口

- **WHEN** 设备引擎需要写一条过程日志
- **THEN** 调用 `utils.logs`，不调用任何 Agent 包内的事件日志函数

### Requirement: 下线的旁路能力不得复活

语音与实时语音会话、知识助手文字问答会话、用例 YAML 模型与用例编写流水线、四分段角色配置 MUST NOT 以兼容或过渡名义恢复。知识库能力 MUST only 保留 `engines/ae_harness/knowledge/` 的只读检索形态：MUST NOT 提供文档上传、写接口或运营面。

#### Scenario: 语音能力零残留

- **WHEN** 扫描 `engines/` 与 `backend/`
- **THEN** 不存在实时语音智能体的构造、语音模型族、语音 WebSocket 路由与语音页面

#### Scenario: 知识库只读

- **WHEN** 检查 `engines/ae_harness/knowledge/`
- **THEN** 只有索引、检索与只读工具，没有上传、删除或写知识库的入口

#### Scenario: 角色配置只有两种文件

- **WHEN** 检查角色与模型的配置落点
- **THEN** 只有 `models.yaml` 与 `prompts/*.md`，不存在 `agent_config.yaml` 或四分段配置类型

### Requirement: 退役状态可机械校验

仓内 MUST 提供静态检查，确认 `engines/agents/` 不存在、全仓无 `engines.agents` 导入、无 `knowledge_assistant` 后端路由与前端模块，并在有人重新引入时点名文件失败。

#### Scenario: 门禁拦截回退

- **WHEN** 有人重新引入 `engines.agents` 的导入或重建该目录
- **THEN** `python run.py check` 失败，且报错点名违规文件

#### Scenario: 下线面检查通过

- **WHEN** 在退役完成的仓库执行 `python run.py check`
- **THEN** 上述静态检查通过，且 `engines/agents` 目录缺失不会引起任何检查报错
