## Context

三个算法簇现状（行号证据）：`device_inspector/service.py:4-228`（XPath 候选与裁剪）、`device_inspector/ocr.py`（79 行，cnocr 双检锁）、`device_pool/pool.py:144-240`（dump_hierarchy 内 XML 解析与设备取数混装）。Step 0 基线已锚定三者行为（85 个测试，经原路径调用）。

## Goals / Non-Goals

**Goals:**

- 三个算法簇平移到 `algorithms/`（函数体一字不改，仅改 import 归属）
- 原处 re-export：既有消费方（inspector views/api、pool 调用方）零改动、行为不变
- D-1 落地：`parse_hierarchy_xml` 纯解析独立，设备取数（3 层 fallback）留 `pool.dump_hierarchy`

**Non-Goals:**

- 不做 dict → `Node`/`OcrText` dataclass 目标契约转换（D-2，后续 change）
- 不给 `algorithms/` 增加任何新算法/新能力
- 不修改 re-export 之外的任何消费方代码（AI 助手等复用方在后续 change 迁移）

## Decisions

- **一字不改平移**：函数体保持原样（含 docstring 中的行号引用仅更新归属说明），保证 diff 可审查
- **re-export 边界**：re-export 只保 `device_inspector` 内部兼容，不成为跨 App import 合法通道（跨 App 应直接 import `algorithms.*`，见 L1a §6.2）
- **pool.dump_hierarchy 拆分**：fallback 循环 + `last_error` 语义保留在 pool；解析段成为 `parse_hierarchy_xml(raw)`；异常文案（"all strategies failed"/"cannot repair"）不变
- **模块级单例照搬**：`ocr._engine/_engine_lock` 平移后保持双检锁（`algorithms/vision/ocr.py` 内的模块态）
- **测试策略**：基线测试经 re-export 全绿 + 新增 identity 冒烟测试（`service.gen_xpath_candidates is algorithms.xpath.gen_xpath_candidates`）

## 模块防火墙自检

- `algorithms/` 零 `apps.*`/`django.*` import（grep 门禁）；`algorithms/vision/ocr.py` 惰性 import cnocr（保持）
- `service.py` 的 re-export 是 App 内部兼容层，不新增跨 App import
- 无 ORM 写路径变化；前端零改动；dashboard 零改动
- 通过

## Risks / Trade-offs

- [re-export 被误当跨 App 通道] → 文档注明 + Step 3b/4 时消费方直接 import algorithms，re-export 逐步退役
- [pool.py 拆分引入行为差异] → 异常文案与解析逻辑一字未改，基线 hierarchy 测试（6 个）直接回归验证
- [ocr 模块态在 tests 中残留] → 双检锁模式原样保留，现有 ocr 基线测试已 mock `_get_engine`
