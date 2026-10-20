## ADDED Requirements

### Requirement: OCR 工具实现保留在引擎工具层且不装配给角色

系统 SHALL 在引擎工具层（`engines/agents/tools`）保留一个只读的 OCR 工具实现，返回文本、置信度、原始角点与归一化中心点。该工具 MUST NOT 被配置进执行模型或验收模型的工具集：基础工具表与所有可开关组都 MUST NOT 包含它。

#### Scenario: 工具实现存在且只读

- **WHEN** 读取引擎工具层的 OCR 工具规格
- **THEN** 存在名为 `ocr_page` 的工具，且标记为只读

#### Scenario: 不装配给任何角色

- **WHEN** 检查执行角色与验收角色的基础工具及可开关组
- **THEN** 其中都不包含 `ocr_page`
