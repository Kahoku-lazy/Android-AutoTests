## Why

页面文本识别仍放在 `utils/vision`，设备检查器与引擎工具各有一条调用链。检查器页面早已不再采集 OCR，但这条后端识别入口还在，和「只由引擎工具识别」的口径不一致。

## What Changes

- 将 `utils/vision` 整包移到 `engines/vision/`。识别函数只允许 `engines/agents/tools/tool_ocr.py` 调用。
- **BREAKING**：删除设备检查器的识别入口。`capture_snapshot` 不再接受 `method=ocr`；白名单不再提供对当前页面执行识别的函数。新抓取不写入 OCR 载荷。
- 保留 `di_snapshots.ocr_json` 与 `ocr_count` 列及历史行的读出。不迁移、不清空存量。

## 关联文档

无独立需求编号。总 PRD 索引提到设备检查器子文档 `PRD-03`，仓库内未见该文件。本变更收紧既有能力，不新增产品需求。

## Capabilities

### New Capabilities

### Modified Capabilities

- `ai-screen-vision`: 页面文本识别只经引擎只读工具暴露，应用层不得再执行识别。
- `device-inspector-page`: 抓取只接受 Dump；`method=ocr` 必须拒绝且不落库。历史 OCR 列保留，新抓取的 OCR 载荷为空。检查器不再提供识别入口。

## Impact

- 引擎：新增 `engines/vision/`；`engines/agents/tools/tool_ocr.py` 改为调用该包。
- 后端：`apps/device_inspector/service.py`、`apps/device_inspector/api.py` 去掉识别执行；`POST /api/inspector/capture` 拒绝非 `dump`。
- 数据：不改表结构。元素定位的页面级 `ocr_json` 不变。
- 测试：引擎 OCR 工具单测保持通过；补一条「只有该工具引用识别包」的源码约束。删除或改写仍指向检查器识别入口的测试。
- 前端：抓取已经固定发 `dump`，不改交互。过时注释与「后端仍接受 ocr」的表述需改掉。
