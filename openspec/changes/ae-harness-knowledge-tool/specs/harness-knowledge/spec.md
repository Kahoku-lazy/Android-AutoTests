## Purpose

为 Harness 提供可独立删除的本地知识库：自带向量模型配置，按库增量建索引，以只读工具形态返回未经改写的检索命中。

## ADDED Requirements

### Requirement: 知识库是零依赖的独立模块

知识库 MUST 位于根级 `engines/ae_harness/knowledge/`，MUST NOT 位于 `tools/`。它 MUST NOT import `engines.ae_harness` 下的其它子包（`agents`、`assistant`、`event`、`middleware`、`workflow`、`tools`）。Harness 其余模块 MUST NOT import 知识库，唯一例外是角色入口处的一处可选导入。

#### Scenario: 删除后其余模块不受影响

- **WHEN** 整目录删除 `engines/ae_harness/knowledge/`
- **THEN** 执行者入口仍能启动并跑任务
- **AND** adb 工具、角色创建、事件记录、SOP 编排行为不变
- **AND** 入口不因缺少知识库而抛异常

#### Scenario: 不反向依赖 Harness 其它模块

- **WHEN** 静态检查 `knowledge/` 下的 import
- **THEN** 不存在对 `engines.ae_harness.agents` / `assistant` / `event` / `middleware` / `workflow` / `tools` 的引用

### Requirement: 自带配置且只允许配置向量模型

知识库 MUST 自带 `config/models.yaml` 与 `config/knowledge_bases.yaml`。`models.yaml` MUST 只接受向量模型条目，字段限定为 `provider` / `api_key` / `model_name` / `dimensions`；出现其它字段、其它模型类别或不支持的 `provider` 时 MUST 装载失败。`agents/config/models.yaml` 与 `agents/models.py` MUST NOT 因本能力被修改。

#### Scenario: 非向量模型条目被拒绝

- **WHEN** `models.yaml` 中出现 `provider: deepseek` 的条目或额外字段
- **THEN** 配置装载失败
- **AND** 错误信息指出违规字段或 provider

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

### Requirement: 探针不调用聊天模型

系统 SHALL 提供 `index` 与 `retrieve` 命令行探针。探针 MUST 直接打印重建数量与原始命中，MUST NOT 创建智能体，也 MUST NOT 调用聊天模型。缺少嵌入配置或参数非法时 MUST 返回非零退出码；仅仅没有命中时 MUST 返回零退出码。

#### Scenario: 无命中不算失败

- **WHEN** 对可用库执行检索探针且没有命中
- **THEN** 探针退出码为 0
- **AND** 输出说明没有命中

#### Scenario: 配置缺失返回非零

- **WHEN** 嵌入密钥缺失或库名不存在
- **THEN** 探针退出码非 0
- **AND** 输出可读原因
