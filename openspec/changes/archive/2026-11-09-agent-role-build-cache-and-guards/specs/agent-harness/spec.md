## MODIFIED Requirements

### Requirement: 模型实例只经单一门面获取

需要模型实例的模块 MUST 只从 `engines/agents/models` 的包入口取实例：MUST NOT 直接 import 该包的子模块，MUST NOT 自行构造 `agentscope` 的聊天、实时语音、嵌入或语音合成模型对象。同一类模型的构造逻辑 MUST 只有一处实现。备用模型的连接参数（`AGENT_FALLBACK_*`）SHALL 由 `models` 解析，重试与回退策略 MUST NOT 自行解析模型连接参数，只接收已建好的备用模型实例。嵌入模型的 token 用量计量 SHALL 由 `models` 提供，调用方只传用量回调。

聊天模型实例 SHALL 由门面按「配置指纹 + 事件循环亲和」复用：同一事件循环内、连接参数（provider / 模型名 / 基础 URL / 密钥 / vision / stream）完全相同的两次取用 MUST 返回同一实例；任一参数变化 MUST 视为不同实例。MUST NOT 在另一个事件循环里复用先前循环建好的实例（异步客户端与循环绑定）。包入口 SHALL 提供显式清空实例复用的手段，供测试隔离环境变量。

#### Scenario: 角色装配只调门面取聊天模型

- **WHEN** 装配任一 LLM 角色
- **THEN** 代码只在包入口调用「按角色键取聊天模型」，装配与工作流代码里不出现 provider、密钥、基础 URL、vision / stream 等连接参数

#### Scenario: 同配置复用同一实例

- **WHEN** 同一次运行内连续装配多个步骤的执行者与验收者
- **THEN** 相同角色键取到的聊天模型是同一对象，不重复构造客户端

#### Scenario: 配置变化即新实例

- **WHEN** 环境变量里的密钥变化，或角色节的 vision / stream / 模型名 / 地址不同
- **THEN** 门面返回新建的实例，不复用旧配置的客户端

#### Scenario: 跨事件循环不复用

- **WHEN** 两个任务在各自线程的事件循环里装配同一角色
- **THEN** 后起的循环拿到新实例，不复用先前循环建好的异步客户端

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

#### Scenario: 复用后的实例不被重复包装

- **WHEN** 门面返回的聊天模型被多次交给装配层
- **THEN** 强制结构化交卷的请求改写只挂一次，模型实例上的调用入口不发生叠加包装

## ADDED Requirements

### Requirement: 角色装配配置严格校验

装载角色四分段时，`agent_config.yaml` 的 `ContextConfig` / `ReActConfig` 节 MUST 只出现对应 dataclass 的字段名：出现未知键 MUST 抛 `ValueError`，且报错 MUST 同时列出未知键与合法键。节点缺失、`null`、空映射、空白字符串仍 SHALL 视为空节并取 dataclass 默认值。`agent_builders` 的 `__all__` MUST 与模块实际定义一致：`__all__` 中的每个名字 MUST 是模块属性。

#### Scenario: 分段键拼写错误立即失败

- **WHEN** 在 `ReActConfig` 下写了 dataclass 不存在的键（如 `max_iter`）
- **THEN** `load_role_spec` 抛 `ValueError`，消息点名该键并给出合法键列表

#### Scenario: 空节仍取默认值

- **WHEN** 某个角色节没有写 `ContextConfig`
- **THEN** 装载结果使用 `ContextConfig` 的默认值，不报错

#### Scenario: 导出清单与实现一致

- **WHEN** 对 `engines.agents.agent_builders` 执行 `import *`
- **THEN** 成功，且 `__all__` 里不存在已删除的符号
