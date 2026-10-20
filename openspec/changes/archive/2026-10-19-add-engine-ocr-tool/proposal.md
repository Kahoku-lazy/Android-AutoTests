## Why

上一单 `retire-ai-toolbox` 删掉了平台侧 OCR 工具（它只经工具箱调试与内部网关可达）。OCR 能力本身仍要保留实现，但按决策改为**只存在于引擎工具层**，且**不装配给任何智能体角色**——这样既不丢失实现，也不改变 SOP 的工具集与模型行为。

## What Changes

- 新增 `engines/agents/tools/tool_ocr.py`：提供只读 `ocr_page(serial, texts="")` 与 `ocr_tool_specs(output_root="")`，经 `engines.device.action` 截图、`utils.vision.ocr.recognize` 识别，返回文本、置信度、原始角点与归一化中心点。
- **不**修改 `engines/agents/tools_config.py`：OCR 不进基础工具、不进可开关组、不进技能目录，任何角色都拿不到它。
- 新增 `tests/engines/agents/test_ocr_tool.py`：守住「工具规格存在且只读」「执行/验收角色均未包含该工具」「文本过滤与中心点归一化」三条不变量。
- 更新 `engines/agents/tools/__init__.py` 的模块说明。
- 无 API、无前端、无数据库变化；引擎运行时行为不变（工具未被装配）。

## 关联文档

产品口头决策「OCR 实现放引擎工具层、不配置给智能体」，无 PRD 编号。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ai-screen-vision`: 新增一条要求——OCR 工具实现保留在引擎工具层、且 MUST NOT 装配进任何角色的工具集。

## Impact

- 引擎：`engines/agents/tools/tool_ocr.py`（新增）、`engines/agents/tools/__init__.py`（说明）。
- 测试：`tests/engines/agents/test_ocr_tool.py`（新增，零设备、零数据库）。
- 不触碰：`tools_config.py`、`engines/agents/role/*`、`apps/*`、前端。
