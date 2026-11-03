## MODIFIED Requirements

### Requirement: 模型配置唯一装载入口

模型连接参数的**代码** SHALL 集中在 `engines/agents/models` 包；模型连接参数的**数据** SHALL 继续留在 `engines/agents/config/data/`（`agent_config.yaml` 的 `ModelConfig` 段与同目录 `config.yaml`），位置与格式 MUST NOT 因本约束而改变，`models` 包内 MUST NOT 存放模型数据文件。角色四分段（Role / Tools / Context / ReAct）的装载 SHALL 留在 `engines/agents/config`，其装载入口 MUST NOT 把模型连接参数回传给角色装配层。`ModelConfig` MUST 止于建模型管线，MUST NOT 成为 Agent 对外构造参数。已删除的 `engines.agents.role.models` MUST NOT 再使用；`engines.agents.config.models` MUST NOT 恢复。

#### Scenario: 装载执行角色模型

- **WHEN** 装配执行角色（`build_ui_executor()` 或等价的角色装配入口）
- **THEN** 模型连接参数取自 `agent_config.yaml` 的 `ModelConfig` 段，经 `engines/agents/models` 读取；角色装配代码里看不到 `ModelConfig` 实例，Agent 构造只接收已建好的模型

#### Scenario: 模型数据仍在 config

- **WHEN** 检查模型数据的落点
- **THEN** 角色与模型数据仍在 `engines/agents/config/data/` 下，`engines/agents/models/` 内没有任何 `.yaml` 数据文件

#### Scenario: 角色装载只回传四分段

- **WHEN** 调用角色装载入口取某个角色的配置
- **THEN** 返回的是角色与三段 Harness 配置，模型连接参数不在返回值里

#### Scenario: 旧模块路径不再存在

- **WHEN** 检查 `engines/agents/config/models.py` 与 `engines/agents/role/models.py`
- **THEN** 两个路径均不存在，且仓内没有对它们的导入

## ADDED Requirements

### Requirement: 模型实例只经单一门面获取

需要模型实例的模块 MUST 只从 `engines/agents/models` 的包入口取实例：MUST NOT 直接 import 该包的子模块，MUST NOT 自行构造 `agentscope` 的聊天、实时语音、嵌入或语音合成模型对象。同一类模型的构造逻辑 MUST 只有一处实现。备用模型的连接参数（`AGENT_FALLBACK_*`）SHALL 由 `models` 解析，重试与回退策略 MUST NOT 自行解析模型连接参数，只接收已建好的备用模型实例。嵌入模型的 token 用量计量 SHALL 由 `models` 提供，调用方只传用量回调。

#### Scenario: 角色装配只调门面取聊天模型

- **WHEN** 装配任一 LLM 角色
- **THEN** 代码只在包入口调用「按角色键取聊天模型」，装配与工作流代码里不出现 provider、密钥、基础 URL、vision / stream 等连接参数

#### Scenario: 备用模型由门面提供

- **WHEN** 环境里配置了 `AGENT_FALLBACK_MODEL`（可选 `AGENT_FALLBACK_PROVIDER` / `AGENT_FALLBACK_BASE_URL` / `AGENT_FALLBACK_API_KEY`）
- **THEN** 包入口返回可用的备用聊天模型实例；未配置模型名时返回空；重试模块不再解析这些变量，只使用传入的实例

#### Scenario: 非聊天模型同样走门面

- **WHEN** 需要 Omni 实时语音、嵌入或语音合成模型
- **THEN** 分别经包入口的对应入口取实例，调用方模块内不出现 `DashScopeRealtimeModel` / `DashScopeEmbeddingModel` / `DashScopeTTSModel` 的构造代码

#### Scenario: 实时语音模型构造只有一处

- **WHEN** 分别检查实时语音角色装配与会话路径取模型的方式
- **THEN** 两条路径走同一处实现，不存在两套并列的 Omni 模型构造

#### Scenario: 门面不被旁路

- **WHEN** 扫描 `engines/` 源码的 import
- **THEN** 包外模块没有 `engines.agents.models.<子模块>` 形式的导入，也没有对 `agentscope.model` / `agentscope.embedding` / `agentscope.tts` / `agentscope.realtime` 模型类的直接构造
