## MODIFIED Requirements

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

## ADDED Requirements

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