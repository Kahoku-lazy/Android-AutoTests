## Why

XPath 候选生成 / XML 解析 / OCR 三个纯算法簇当前埋在 App 内部实现里：`apps/device_inspector/service.py`（gen_xpath_candidates/trim_hierarchy）、`apps/device_inspector/ocr.py`（OCR）、`apps/device_pool/pool.py::dump_hierarchy`（XML 解析与设备取数混装）。防火墙禁止跨 App import `service`，导致 AI 助手、用例管理等复用方只能复制或违规 import。这是 L1a 详档 §一/§二 的迁移动因，也是 L2/L1c 后续消费算法能力的前置。

## What Changes

- 新建顶级包 `algorithms/`（零 `apps.*`/`django.*` 依赖，纯函数）：
  - `algorithms/xpath.py`：`gen_xpath_candidates` / `trim_hierarchy` / `_LAYOUT_VIEWGROUPS` / `_simple_class` / `_has_identity` / `_specificity`（自 `device_inspector/service.py:4-228` 平移）
  - `algorithms/hierarchy.py`：`parse_hierarchy_xml(raw)`（自 `device_pool/pool.py:175-240` 纯解析部分抽出，D-1 边界：设备取数 3 层 fallback 留在设备侧）
  - `algorithms/vision/ocr.py`：`recognize` / `_get_engine` / `_pil_to_b64`（自 `device_inspector/ocr.py` 平移，保持双检锁惰性加载）
- **原处 re-export 保兼容**（无行为变化铁律）：`service.py` 头、`ocr.py`、`pool.dump_hierarchy` 改调 `algorithms.*`，既有消费方零改动
- 数据契约维持现状 dict（`Node` dataclass 目标契约归 D-2 后续演进，本变更只平移不改结构）
- 新增 `tests/algorithms/test_package_smoke.py`：三模块直导冒烟 + re-export 对象同一性断言

## 关联文档

- ARCH：`dev_docs/03-设计与架构/设计-L1a-算法层.md`（§六 迁移映射 11 项、§6.2 re-export 策略、D-1/D-2 决策）
- ARCH：`dev_docs/03-设计与架构/设计-目标架构-设备交互协议与引擎分层.md`（§2.5 算法层职责、§三 防火墙 algorithms 行）
- 基线：OpenSpec 已归档 `2026-08-20-refactor-baseline-tests`（本变更后其断言经 re-export 继续生效）
- 无 PRD 变更（纯搬家 + re-export，无需求级行为变化）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯重构（无行为变化的大搬家 + re-export）：`.openspec.yaml` 已设 `skip_specs: true`。注：项目纪律默认拒绝无测试保护的大搬家，本变更在 Step 0 基线（85 个锚定测试）保护下执行。

## Impact

- 新增：`algorithms/{__init__,xpath,hierarchy}.py`、`algorithms/vision/{__init__,ocr}.py`、`tests/algorithms/test_package_smoke.py`
- 修改：`apps/device_inspector/service.py`（头 228 行改 re-export）、`apps/device_inspector/ocr.py`（整体变 re-export）、`apps/device_pool/pool.py`（dump_hierarchy 纯解析段改调 algorithms）
- 前端零改动；数据库零改动
