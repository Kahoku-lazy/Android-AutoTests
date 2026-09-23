## Context

- `algorithms/` 是 L1a 纯算法包（零 `apps.*` / 零 `django.*`），被 `apps/device_inspector` 与 `dev_docs/Agent Skill 技能/device-page-analysis` 脚本消费。
- OCR 现状：`recognize(screenshot_path)`（`algorithms/vision/ocr.py:40-88`）逐条 `_pil_to_b64(img.crop(...))`；调用方只有 `service.capture_ocr_payload`（`service.py:169`）与 `service.ocr_page_payload`（`service.py:231`）。
- 分层现状：`build_layers(nodes, include_candidates=False)`；`element_entry` 仅在 `include_candidates` 为真时追加 `xpath_candidates`。
- 规格现状：`element-layering` 的「元素条目携带坐标与状态」写「主定位与候选定位列表」；`device-inspector-layers` 的「分层查询返回元素条目」写「响应 MUST NOT 携带每个元素的候选定位列表」。两条并存，靠 `include_candidates=False` 分隔。

## Goals / Non-Goals

**Goals:**

- 删掉两处无生产调用方的算法代码及其运行时代价。
- 让 `element-layering` 与 `device-inspector-layers` 的条目口径不再互相矛盾。

**Non-Goals:**

- 不动 `gen_xpath_candidates`（候选生成仍是公开能力）。
- 不动分层接口的响应体（本来就只给主定位）、不动 OCR 的响应契约（本来就只要文本/置信度/坐标/中心点）。
- 不复活「候选按需单独查询」端点（`add-layers-api-and-node-index` 的 D7 提过，从未建立；不在本变更范围）。

## Decisions

**D1 OCR 侧删的是「产出」，不是「过滤」。** 两处 `pop` 只会剥离 `recognize()` 自己生产的键；产出删掉后 `pop` 恒为空操作。保留一个永真的防御性 `pop`，等于把「契约由调用方兜底」写进代码，而真实契约由 `ai-screen-vision` 与单测的字段断言守护。备选：只删产出、保留 `pop` → 否决（留下解释「为什么过滤一个不存在的字段」的死代码）。

**D2 候选列表分支整体删除，而不是保留形参等未来端点。** 该分支自 `add-layers-api-and-node-index` 起就没有调用方，D7 承诺的「候选按需单独查询」也未落地；保留形参会让「条目到底带不带候选」出现两份真相（形参可开 + 规格说 MUST NOT）。备选：保留形参 → 否决（`element-layering` 与 `device-inspector-layers` 的矛盾会继续挂着）。

**D3 矛盾由算法侧规格让步。** 候选始终能从节点集合重算（`gen_xpath_candidates` 是纯函数），把「候选列表」写进条目契约只会诱导调用方自行挑选定位 —— 这正是 `device-inspector-layers` 明令禁止的第二处口径。故 `element-layering` 的条目字段清单改为「主定位」，并补一条 MUST NOT 携带候选的场景。备选：改 `device-inspector-layers` 允许携带候选 → 否决（会把响应体从 82.8 KB 推回 134.6 KB，且重新打开「调用方自挑定位」的口子）。

## 模块防火墙自检

- **算法层依赖**：不新增 import；删除后 `algorithms/` 仍是零 `apps.*` / 零 `django.*`。
- **跨 App / 写库**：不涉及。
- **前端 HTTP 出口**：零改动。

## Risks / Trade-offs

- [将来需要「每个元素的全部候选」] → `gen_xpath_candidates(el, all_els)` 仍可直接调用；需要走接口时再按 D7 建独立端点，不靠条目字段承载。
- [`capture_ocr_payload` 的 `ocr_json` 少了两个键] → 不会：这两个键在落库前就被剥离，历史 `ocr_json` 本来就不含它们。
- [仓外消费方依赖 `recognize()` 的 `thumbnail` 键] → 已核实仓内无：`grep thumbnail` 在 `algorithms/` 外只命中元素缩略图的 `thumbnail_path`；`device-page-analysis` 脚本不调用 OCR。

## Open Questions

无。
