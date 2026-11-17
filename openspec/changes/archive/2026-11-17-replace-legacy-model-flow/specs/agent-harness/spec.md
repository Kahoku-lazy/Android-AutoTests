## MODIFIED Requirements

### Requirement: 模型配置唯一装载入口

模型连接参数的数据 SHALL 只存在于配置层读出的模型表；读取该表与密钥加解密 MUST 只有配置层一处实现。模型实例的创建 MUST 由模型创建层按短名完成，创建层 MUST NOT 自己读文件或环境变量。角色四分段（Role / Tools / Context / ReAct）的装载 SHALL 留在配置层，其装载入口 MUST NOT 把模型连接参数回传给角色装配层。`ModelConfig` MUST 止于建模型管线，MUST NOT 成为 Agent 对外构造参数。已删除的 `engines.agents.role.models` 与 `engines.agents.config.models` MUST NOT 恢复。旧模型包 `engines/agents/models` MUST NOT 继续作为装载入口存在。

#### Scenario: 装载执行角色模型

- **WHEN** 装配执行角色（`build_ui_executor()` 或等价的角色装配入口）
- **THEN** 模型短名取自角色配置，模型实例由模型创建层按短名创建；角色装配代码里看不到连接参数，Agent 构造只接收已建好的模型

#### Scenario: 模型数据仍在 config

- **WHEN** 检查模型数据的落点
- **THEN** 角色与模型数据仍由配置层读取，模型创建层内没有任何模型数据文件

#### Scenario: 角色装载只回传四分段

- **WHEN** 调用角色装载入口取某个角色的配置
- **THEN** 返回的是角色与三段 Harness 配置，模型连接参数不在返回值里

#### Scenario: 旧模块路径不再存在

- **WHEN** 检查 `engines/agents/config/models.py`、`engines/agents/role/models.py` 与 `engines/agents/models/`
- **THEN** 这些路径均不存在，且仓内没有对它们的导入

### Requirement: 模型实例只经单一门面获取

需要模型实例的模块 MUST 只经模型创建层的唯一出口按短名创建：MUST NOT 直接 import 该层的内部模块，MUST NOT 自行构造聊天、实时语音、嵌入或语音合成模型对象。同一类模型的构造逻辑 MUST 只有一处实现。查看规格 MUST 走只读视图，MUST NOT 为了读字段而创建实例。

聊天模型实例 SHALL 在同一进程内按「短名 + 流式开关」复用：这两项相同的两次创建 MUST 把同一聊天模型交给不同的新智能体。实时语音模型 MUST NOT 复用。创建层 MUST NOT 读取调用点传入的明文密钥来绕过配置层注入的密钥。

备用模型的连接参数 MUST NOT 再由模型创建层解析。重试与回退策略 MUST NOT 自行解析模型连接参数；只在调用方已经传入备用模型实例时使用该实例。嵌入模型的 token 用量计量 MUST 由检索调用方在创建之后自行记录，MUST NOT 作为模型创建出口的参数。

强制结构化交卷时关闭思考的行为 SHALL 保留，且 MUST 只生效一次：同一聊天模型被多次交给装配层时，不得叠加包装。该行为 MUST NOT 放在模型创建出口内。

#### Scenario: 角色装配只调门面取聊天模型

- **WHEN** 装配任一 LLM 角色
- **THEN** 代码按角色键经聊天创建出口取智能体，装配与工作流代码里不出现 provider、密钥、基础 URL 等连接参数

#### Scenario: 同配置复用同一实例

- **WHEN** 同一次运行内连续装配多个使用同一聊天短名、同一流式开关的角色
- **THEN** 这些角色拿到同一聊天模型对象，各自仍是新的智能体实例

#### Scenario: 配置变化即新实例

- **WHEN** 同一聊天短名一次要求流式、一次要求非流式
- **THEN** 两次拿到的聊天模型不是同一对象

#### Scenario: 跨事件循环不复用

- **WHEN** 两个任务在各自线程的事件循环里装配同一角色，且短名与流式开关相同
- **THEN** 聊天模型按短名与流式开关复用，不按事件循环拆分；两个智能体仍是新实例

#### Scenario: 备用模型由门面提供

- **WHEN** 主模型因瞬态故障用尽重试，且调用方没有传入备用模型实例
- **THEN** 重试模块不自行解析备用模型配置，也不尝试其它模型

#### Scenario: 非聊天模型同样走门面

- **WHEN** 需要 Omni 实时语音或嵌入模型实例
- **THEN** 经模型创建层按短名创建，调用方模块内不出现这些模型类的构造代码

#### Scenario: 实时语音模型构造只有一处

- **WHEN** 分别检查实时语音角色装配与会话路径取模型的方式
- **THEN** 两条路径走同一处实现，不存在两套并列的 Omni 模型构造

#### Scenario: 门面不被旁路

- **WHEN** 扫描 `engines/` 源码的 import
- **THEN** 包外模块没有模型创建层子模块形式的导入，也没有对聊天、嵌入、语音合成、实时语音模型类的直接构造

#### Scenario: 复用后的实例不被重复包装

- **WHEN** 同一聊天模型被多次交给装配层，并触发强制结构化交卷
- **THEN** 关闭思考的改写只生效一次，模型调用入口不发生叠加包装
