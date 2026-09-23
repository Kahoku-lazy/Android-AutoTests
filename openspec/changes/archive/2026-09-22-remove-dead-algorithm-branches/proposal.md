## Why

`algorithms/` 里有两处**没有任何生产调用方**的代码，仍在每次采集/查询时付出代价：

1. **OCR 的 base64 缩略图**（`algorithms/vision/ocr.py`）。`recognize()` 给每条文本裁一张图、编成 base64 JPEG，但两个调用方**都丢弃它**：`service.py:174-175` 显式 `pop` 掉两个键，`service.py:231-249` 只读 `text` / `confidence` / `coordinates`。平台契约（`ai-screen-vision`）也只要文本、置信度、坐标与归一化中心点。代价是每次 OCR 对每条文本块做一次 PIL crop + JPEG 编码 + base64（整页 20+ 条 → 20+ 次）。这是「前端内嵌 base64 缩略图」时代的遗留。
2. **分层算法的候选定位列表分支**（`algorithms/element_layers.py` 的 `include_candidates`）。生产唯一调用方 `api.py:288` 用默认值，唯一传 `True` 的是单测。归档变更 `add-layers-api-and-node-index` 的 D7 写的是「候选**按需单独查询**」，但那个独立查询从未建立；真正流向元素定位的候选走的是采集期落盘的 `dump_json.elements[].xpaths`（`service.py:91` → `element_locator/api_snapshot.py:228`），与本分支无关。

本变更同时消解一处**规格自相矛盾**：`element-layering` 要求元素条目 MUST 携带「主定位与候选定位列表」，而 `device-inspector-layers` 要求响应 MUST NOT 携带候选定位列表。`include_candidates` 默认关闭正是为同时满足两者，但算法侧那条要求已无实现意义 —— 候选始终可由 `gen_xpath_candidates` 按需重算。

## What Changes

- **删除 OCR 结果里的 base64 缩略图**：`recognize()` 不再裁图、不再编码、不再返回 `thumbnail` / `thumbnail_format`；调用方两处为剥离而写的 `pop` 与注释一并删除。
- **删除分层算法的候选列表分支**：`build_layers` / `element_entry` 的 `include_candidates` 形参与 `xpath_candidates` 输出分支删除；元素条目恒只带一条主定位。
- **MODIFIED（`element-layering`）**：元素条目的字段清单去掉「候选定位列表」，并补一个「候选定位列表 MUST NOT 出现在条目里」的场景，使该能力与 `device-inspector-layers` 的口径一致。
- 候选生成能力本身**不受影响**：`gen_xpath_candidates` 仍是公开纯函数，采集期的 `xpaths` 仍原样落盘并流向元素定位。

## 关联文档

- PRD-03（设备检查器）

## Capabilities

### Modified Capabilities

- `element-layering`: 「元素条目携带坐标与状态」的字段清单由「主定位与候选定位列表」改为「主定位」，并新增「条目不含候选定位列表」场景。

## Impact

- 算法层：`algorithms/vision/ocr.py`（去掉 base64 缩略图）、`algorithms/element_layers.py`（去掉候选列表分支）
- 后端：`apps/device_inspector/service.py`（去掉两处已成为空操作的 `pop` 与相应注释）
- 测试：`tests/graybox/unit/test_inspector_ocr_tool.py`（桩输入不再伪造缩略图键）、`tests/graybox/unit/test_element_layers.py`（去掉 `include_candidates=True` 断言）
- 不涉及：接口契约与响应体（分层响应本来就不含候选，OCR 工具响应本来就不含缩略图）、前端、设备交互
