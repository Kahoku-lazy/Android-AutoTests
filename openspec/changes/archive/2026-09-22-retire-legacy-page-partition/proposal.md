## Why

`algorithms/layout.py`（170 行）是第一代「页面结构分析」的纯规则分区算法（6 层分区 + WebView 识别 + 指标），已被两级分层（`algorithms/element_layers.py`，变更 `add-element-layering-core`）取代。核实结论（非推测）：

- 它唯一的活链路是 `GET /api/inspector/snapshots/{id}/analyze/`：`service.analyze_snapshot_payload` → `api.analyze_snapshot` → `views.snapshot_analyze` → `urls.py`。
- 该端点**没有任何产品入口**：`frontend/src` 全目录 `grep analyze` = **0**（前端在变更 `rework-inspector-layers-view` 中已把 `analyzeSnapshot` 移出调用链，改用分层端点）；AI 工具箱 `apps/ai_assistant/tools.py` 的 `TOOL_META` 共 11 个工具，**没有页面分析工具**。
- 它**零单测**：`grep classify_structure tests/` = 0，无 `test_layout*.py`。
- 同一功能的语义层也已孤儿：`apps/ai_assistant/llm_semantic.py` 的 `validate_semantic` 零调用方、零测试（`tests/ai_assistant/` 目录不存在）。

`openspec/specs/page-analysis-semantic` 的 5 条需求全部只由这两处载体支撑 —— 载体一去，能力即失去载体。本次把它们同批退役。

## What Changes

### 1. 删除第一代纯规则分区

- 删除 `algorithms/layout.py` 与 `apps/device_inspector/service.py` 的 `analyze_snapshot_payload`（及其 `classify_structure` import）。

### 2. 退役端点 `GET /api/inspector/snapshots/{id}/analyze/`

- 删除 `apps/device_inspector/api.py` 的 `analyze_snapshot`（含 `__all__` 条目）、`views.py` 的 `snapshot_analyze`、`urls.py` 的 import 与路由。
- 删除 `tests/api/case/inspector.yaml` 中该端点的两条用例（TC-INS-004 / TC-INS-040）。

### 3. 删除孤儿语义层

- 删除 `apps/ai_assistant/llm_semantic.py`（`validate_semantic`，零调用方零测试）。

### 4. 能力退役：`page-analysis-semantic`

- 该 spec 的 5 条需求全部进入 `REMOVED Requirements`（含 Reason 与 Migration）。

### 5. 文档同步

- 接口文档：端点全集 9 → 8，删总览行与第 6 节，其后各节重新编号，并修正受影响的「第 N 节」交叉引用。
- PRD-03：删除该端点的契约块、代码指针、2 条 TC 行，并把「可重试来源五类」修正为四类。
- 总体架构图的 `algorithms/` 节点去掉 `layout`。

### 6. **BREAKING**

- 接口：`GET /api/inspector/snapshots/{id}/analyze/` 及其子路径一律 404。
- 规格：`page-analysis-semantic` 能力退役，主 spec 由归档流程删除。

## 明确移出本变更范围

- **不动分层查询端点**与 `algorithms/element_layers.py` / `xpath.py` / `hierarchy.py` / `vision/ocr.py`。
- **不动前端**：前端早已不调用该端点，本变更不产生前端改动。
- **不修 `openspec/specs/ai-platform-task` 第 22 行的 `analyze_page` / `save_page_semantic` 场景**：该场景引用的 AI 工具在当前工具注册表中本就不存在（先于本变更的事实），属既有规格漂移，另议。
- **不做 PRD-03 的整体刷新**：该文档的 §结构分析 仍按第一代「分区筹码 / 筛选 / 固定 7 行」叙述，落后于实现，另开；本次只修本变更使其失效的部分。

## 关联文档

- PRD-03（设备检查器）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `page-analysis-semantic`：**整能力退役** —— 该 spec 全部 5 条需求进入 REMOVED（含 Reason 与 Migration），归档后主 spec 删除，不留空壳。

## Impact

- **算法层 1 个文件删除**：`algorithms/layout.py`（170 行）
- **后端 5 个文件**：`device_inspector` 的 `service.py` / `api.py` / `views.py` / `urls.py`；`ai_assistant/llm_semantic.py`（整文件删除）
- **接口**：端点 9 → 8；`/api/inspector/snapshots/{id}/analyze/` 404
- **测试**：`tests/api/case/inspector.yaml` 由 16 条降为 14 条；`test_api_path_callers.py` 的 yaml 面实测同步下降（下限 42，需复核）
- **文档 3 个**：`API-设备检查器.md`、`PRD-03-设备检查器.md`、`ARCH-平台总体架构.md`
- **DB**：无模型/无迁移、无数据变更
