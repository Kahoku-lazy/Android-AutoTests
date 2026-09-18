## Purpose

页面结构分析的 LLM 语义增强：在纯规则 6 层分区骨架之上，由 AI 助手对页面元素生成中文功能名、识别重复卡片结构、总结页面意图，并在语义提交时校验防幻觉、保证纯规则结果始终可用。

## ADDED Requirements

### Requirement: 纯规则结构分析独立可用

系统 SHALL 提供不依赖 LLM 的纯规则结构分析结果（6 层分区、XPath、交互指标），供前端按钮与 AI 工具直接使用。

#### Scenario: 纯规则分析返回
- **WHEN** 用户或 AI 工具请求结构分析
- **THEN** 返回 6 层分区、每元素 role/metrics/xpath，不依赖 LLM

### Requirement: 元素功能名命名

系统 SHALL 支持对带 resource-id 的元素生成中文功能名（如 `ivGateway` → 网关入口、`ivSwitch` → 开关）。

#### Scenario: 提交功能名
- **WHEN** AI 助手提交语义命名（元素 resource_id 与对应 func_name）
- **THEN** 该元素的结果包含非空 `func_name` 字段

### Requirement: 语义提交校验

系统 MUST 在语义提交时校验 resource_id 真实性，拒绝输入元素集合中不存在的 resource_id。

#### Scenario: 拒绝幻觉命名
- **WHEN** 语义提交包含了快照元素集合中不存在的 `resource_id`
- **THEN** 该条命名的 `func_name` 被置空，不产生虚假功能名

#### Scenario: 指标枚举校验
- **WHEN** 语义提交的 metrics 包含枚举外取值（非 可点击/可滚动/可勾选）
- **THEN** 该非法取值被剔除，不写入结果

### Requirement: 页面意图总结

系统 SHALL 支持提交一句页面意图总结。

#### Scenario: 生成页面摘要
- **WHEN** AI 助手提交 page_summary
- **THEN** 结果包含 `page_summary` 字段

### Requirement: 卡片角色识别

系统 SHALL 支持识别页面中重复的卡片结构，并标注每张卡片内元素承担的角色（名称、状态、开关、连接图标等）。

#### Scenario: 识别设备卡片
- **WHEN** 页面存在结构重复的卡片（如设备列表）
- **THEN** 结果包含 `cards` 数组，每项含卡片名称与字段角色映射
