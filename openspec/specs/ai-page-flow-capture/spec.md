# ai-page-flow-capture Specification

## Purpose
TBD - created by archiving change add-ai-page-flow-capture. Update Purpose after archive.
## Requirements
### Requirement: 元素可带别名保存到元素定位

系统 SHALL 允许 AI 智能体在保存页面元素时指定每个元素的中文别名；未指定别名时 SHALL 回退为元素 text 或 resource_id。别名用于标识页面组件与元素定位，供用例编写引用。

#### Scenario: 带别名保存元素

- **WHEN** AI 智能体保存页面元素并传入别名（如 `ivSwitch → 设备开关`）
- **THEN** 该别名写入元素记录的 `alias` 字段

#### Scenario: 未指定别名回退

- **WHEN** AI 智能体保存元素但未指定别名
- **THEN** 别名回退为该元素的 text 或 resource_id

### Requirement: 页面跳转关系幂等落库

系统 SHALL 提供幂等的页面跳转关系写入能力：同一「起始页 → 目标页 → 触发元素」重复写入时 SHALL 复用已有记录，不产生重复边。

#### Scenario: 重复写入同一条边

- **WHEN** AI 智能体对已存在的「from_page → to_page + trigger_element」再次建边
- **THEN** 返回已有记录，不新增重复的 `el_page_flows` 行

### Requirement: 生成工作流页面流文档

系统 SHALL 提供受控写图能力：AI 智能体提交结构化「起始包名 + 页面 + 跳转边」数据，系统 SHALL 编译为 VueFlow `config_json`（起点「启动 App」节点 + 页面节点，跳转元素作为页面节点的 navigation 输出口指向目标页面节点）并落库为 `wf_documents`（`doc_type=page_flow`）。

#### Scenario: 生成页面流文档

- **WHEN** AI 智能体提交起始包名、页面列表与跳转边
- **THEN** 生成一个页面流文档，起点为「启动 App」，主页节点带跳转元素的 navigation 输出口指向目标页面节点

#### Scenario: 无跳转元素不生成输出口

- **WHEN** 某页面的元素均不触发页面跳转
- **THEN** 该页面节点不生成 navigation 输出口（仅记录为页面节点）

