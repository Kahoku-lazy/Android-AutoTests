# harness-knowledge Specification

## Purpose
为 Harness 提供可独立删除的本地知识库：自带向量模型配置，按库增量建索引，以只读工具形态返回未经改写的检索命中。

## Requirements

### Requirement: 知识库是零依赖的独立模块

知识库 MUST 位于根级 `engines/ae_harness/knowledge/`，MUST NOT 位于 `tools/`。它 MUST NOT import `engines.ae_harness` 下的其它子包（`agents`、`assistant`、`event`、`middleware`、`workflow`、`tools`）。ae_harness 内其它子包 MUST NOT import 知识库：挂载到 Agent 的效果评测完成前，Harness 内部引用数 MUST 为零。平台 backend MAY 经局部可选导入使用知识库的只读检索与用量出口（行为见 `knowledge-search-entry`）；该引用 MUST NOT 计入 Harness 内部引用数，MUST NOT 使知识库反向依赖平台，且 MUST 保持整目录删除后平台降级不炸。

#### Scenario: 删除后其余模块不受影响

- **WHEN** 整目录删除 `engines/ae_harness/knowledge/`
- **THEN** 执行者入口仍能启动并跑任务
- **AND** adb 工具、角色创建、事件记录、SOP 编排行为不变
- **AND** 入口不因缺少知识库而抛异常

#### Scenario: 不反向依赖 Harness 其它模块

- **WHEN** 静态检查 `knowledge/` 下的 import
- **THEN** 不存在对 `engines.ae_harness.agents` / `assistant` / `event` / `middleware` / `workflow` / `tools` 的引用

#### Scenario: 平台桥接不破坏独立性守护

- **WHEN** backend 经局部可选导入引用知识库的检索与用量出口
- **THEN** Harness 内部零引用守护测试仍通过
- **AND** 整目录删除后平台提问降级为「检索不可用」，不抛 500

### Requirement: 自带配置且只允许配置向量模型

知识库 MUST NOT 再携带向量模型文件或库目录文件。向量模型参数与库列表 MUST 由调用方传入：向量模型参数限定为 `provider` / `api_key` / `model_name` / `dimensions`，且 `provider` 只接受受支持的向量厂商；出现其它字段、其它模型类别或不支持的厂商时 MUST 拒绝创建。库列表的每一项 MUST 含库名、说明、只读资料目录与启用状态，两个启用库的资料目录 MUST NOT 相同或互相包含。知识库 MUST NOT 读取平台数据库，也 MUST NOT import 平台代码。聊天模型创建层与 `agents/` MUST NOT 因本能力被修改。

#### Scenario: 调用方传入向量模型

- **WHEN** 调用方传入受支持厂商的向量模型参数与合法库列表
- **THEN** 知识库按该模型建索引并检索
- **AND** 不读取任何自带 yaml

#### Scenario: 非向量模型条目被拒绝

- **WHEN** 传入的向量模型参数含聊天、实时语音或语音合成字段，或厂商不受支持
- **THEN** 创建失败
- **AND** 错误信息指出违规字段或厂商

#### Scenario: 密钥不以明文出现

- **WHEN** 嵌入模型创建成功或失败
- **THEN** 错误信息与返回值只含环境变量名
- **AND** 不包含密钥明文

### Requirement: 按库增量索引

系统 MUST 只索引 `.md` 与 `.txt`。每个启用库 MUST 有唯一名称与只读资料目录，两个启用库的资料目录 MUST NOT 相同或互相包含。未变化文件（修改时间、大小、切块版本均一致）MUST NOT 重复嵌入；资料目录中已删除的文件 MUST 从索引中移除。单库索引失败 MUST NOT 中断调用方。

#### Scenario: 未变化文件跳过嵌入

- **WHEN** 文件修改时间、大小与切块版本都未变化
- **THEN** 本次索引跳过该文件
- **AND** 不再次调用嵌入模型

#### Scenario: 目录冲突被拒绝

- **WHEN** 两个启用库的资料目录相同或互相包含
- **THEN** 库目录装载失败并指出冲突的库名

### Requirement: 检索只返回结构化命中并支持两项筛选

检索 MUST 接受一个查询、可选的库名、`top_k` 与相似度阈值。不指定库名时 MUST 检索全部启用库并合并排序。每条命中 MUST 包含库名、来源文件、文档编号、片段序号、相似度与未经改写的正文。低于阈值的结果 MUST 被丢弃。库不存在、库被禁用或检索失败时 MUST 返回空结果与可读原因，MUST NOT 抛出异常。

#### Scenario: 命中包含验收字段

- **WHEN** 对可用库检索且存在高于阈值的片段
- **THEN** 每条结果都包含库名、来源文件、片段序号、相似度与正文
- **AND** 正文不包含模型生成的总结

#### Scenario: 无命中与检索不可用可区分

- **WHEN** 库可用但没有达到阈值的片段
- **THEN** 返回空命中并标记为「无命中」

- **WHEN** 嵌入配置缺失或索引失败
- **THEN** 返回空命中并标记为「检索不可用」及原因
- **AND** 两种情况在工具返回文案上不同

### Requirement: 只读工具并且只在调用时工作

知识库 MUST 以只读工具形态交付：`build_knowledge_tools()` 返回 `FunctionTool` 列表，由调用方挂载。import 该模块 MUST NOT 读配置、连数据库或建索引；初始化 MUST 发生在首次工具调用。工具返回 MUST 遵循 Harness 工具返回契约：成功含 `timestamp` 与 `status: true`，失败含 `timestamp` 与 `status: false`。

#### Scenario: import 无副作用

- **WHEN** 只 import 知识库模块并调用 `build_knowledge_tools()`
- **THEN** 不读取任何 yaml、不创建 SQLite 文件、不调用嵌入模型

#### Scenario: 工具只读

- **WHEN** 检查工具标记
- **THEN** `is_read_only` 为真
- **AND** 权限判定为放行

### Requirement: 嵌入用量出口

知识库 SHALL 导出嵌入调用的 token 用量：每次真实发生的嵌入模型调用产出一条用量事件，字段 MUST 含模型名、密钥环境变量名（只有名字，MUST NOT 含密钥明文）、token 数、耗时、阶段（索引 / 检索）与库名。用量记录 MUST NOT 改变检索行为、命中字段与三态文案；token 为 0 或空的调用 SHALL NOT 产出事件。用量出口 MUST NOT import Harness 其它子包，MUST NOT 写资料目录，MUST NOT 把检索改写成生成。

#### Scenario: 用量事件字段齐全

- **WHEN** 一次检索触发查询嵌入
- **THEN** 用量出口给出一条事件，含模型名、密钥环境变量名、token 数、耗时、阶段与库名
- **AND** 事件与返回值不含密钥明文

#### Scenario: 检索行为不因用量记录改变

- **WHEN** 对同一查询分别在有用量出口与无用量出口下检索
- **THEN** 命中字段、排序与 ok / no_hit / unavailable 三态文案一致

#### Scenario: 零 token 不产出事件

- **WHEN** 嵌入调用返回 token 为 0 或空（如空输入）
- **THEN** 用量出口不产出事件

#### Scenario: 用量出口不破坏独立性

- **WHEN** 静态检查用量出口实现的 import
- **THEN** 只依赖 agentscope 与标准库，不出现 Harness 其它子包
