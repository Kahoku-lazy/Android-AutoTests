## REMOVED Requirements

### Requirement: 纯规则结构分析独立可用

**Reason**: 该需求的载体是第一代 6 层页面分区（`algorithms/layout.py` 的 `classify_structure`）与端点 `GET /api/inspector/snapshots/{id}/analyze/`。核实结论：前端自变更 `rework-inspector-layers-view` 起已改用分层端点（`frontend/src` 全目录 `grep analyze` = 0），AI 工具箱 11 个工具中无页面分析工具，该端点无任何产品入口，其算法模块亦零单测。

**Migration**: 页面结构改由分层查询端点 `GET /api/inspector/snapshots/{id}/layers/` 提供（规格 `device-inspector-layers`），按「布局容器 / 滚动·集合容器 / 内容控件 / 其它」两级分组，每个元素给出一条主定位。需要 XPath 候选时调用纯函数 `algorithms.xpath.gen_xpath_candidates`。

### Requirement: 元素功能名命名

**Reason**: 唯一实现是 AI 工具 `save_page_semantic` 的 handler，而该工具在当前工具注册表（`apps/ai_assistant/tools.py` 的 `TOOL_META`，共 11 个）中不存在；其校验实现 `apps/ai_assistant/llm_semantic.py` 零调用方、零测试。

**Migration**: 元素中文别名改由设备检查器的内联重命名（`nameOverrides` → `element_aliases`，经 `save-elements` 落库）与元素定位页面的手工编辑承担。

### Requirement: 语义提交校验

**Reason**: 唯一实现是 `apps/ai_assistant/llm_semantic.validate_semantic`，全仓零调用方，且 `tests/ai_assistant/` 不存在。语义提交通道（`save_page_semantic` 工具）本就不在注册表中，该校验没有可守护的入口。

**Migration**: 无替代载体。LLM 语义命名不再有提交面；元素写入只经设备检查器与元素定位的人工路径。

### Requirement: 页面意图总结

**Reason**: 与「语义提交校验」同源 —— 承载它的 `save_page_semantic` 工具不存在，校验模块无调用方。

**Migration**: 无替代载体；页面意图由人在用例与页面资产的人工描述中表达。

### Requirement: 卡片角色识别

**Reason**: 承载它的 `save_page_semantic` 工具不存在，校验模块无调用方；该能力的输出（`cards` 数组）没有任何下游消费者。

**Migration**: 无替代载体。
