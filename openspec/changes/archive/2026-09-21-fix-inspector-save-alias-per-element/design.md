## Context

- 串名链路：`store.ts` 的 `saveToElements` 用 `nameOverrides`（键为元素 `_idx`）构造 `aliases = {resource_id: name}`（同名 rid 后者覆盖前者）→ 后端按 rid 回填（`api.py:293-297`）→ 元素定位 `import_snapshot_page` 写 `alias`。**下标信息在组装成 rid 映射时就被丢掉了**，这是根因。
- 既有契约：`save_snapshot_to_elements(..., aliases=None)` 的 rid 口径同时被 AI 助手工具 `save_page_to_elements` 使用（归档变更 `2026-09-02-add-ai-page-flow-capture` 引入），因此不能改其语义。
- `element_ids` 已是「按 dump 下标」的口径（`api.py:286-291`），逐元素名称沿用同一坐标系最自然。
- 前端 `nameOverrides` 的键就是 `_idx`（= dump 下标，见 `store.ts` 的 `setElementName` 与 `StructureAnalysisPanel.nameValue`），无需转换。

## Goals / Non-Goals

**Goals:**

- 每个元素的自定义名只落到它自己身上
- 不破坏 AI 工具与旧请求形状

**Non-Goals:**

- 不改 rid 口径的语义（仍可整体按 rid 命名）
- 不改元素定位的回退规则与 UI

## Decisions

**D1 新增 `element_aliases: [{index, name}]` 而不是改 `aliases` 的键**
理由：`aliases` 的 rid 口径有第二个调用方（AI 工具），改键等于破坏它；新增字段是向后兼容的最小改动，且 `index` 与 `element_ids` 同源、语义一致。
备选：把 `aliases` 改成 `{index: name}` → 否决（破坏 AI 工具与既有前端版本）。

**D2 回填顺序：先 rid 别名、后逐元素别名**
理由：同一请求里若两个口径都给了同一个元素，更具体的「逐元素」应胜出。

**D3 逐元素回填按**原始**下标，而不是筛减后的位置**
实现上先构造 `pairs = [(原始下标, 元素)]`（`element_ids` 存在时按其筛减）再 `selected = [dict(e) for _, e in pairs]`，回填时用 `pairs` 里的原始下标查 `element_aliases`。若用筛减后的位置查，勾选子集时会整体错位。
备选：在筛减前先把别名写进元素副本 → 可行但会让「只勾选部分元素」时把未勾选元素的别名也带进 `selected` 的源数据，边界更绕；按原始下标回填最直白。

**D4 前端停止发送 rid 口径的 `aliases`**
理由：检查器的改名是逐元素的，再发一份 rid 映射只会把同一个名字扩散到同 rid 的其它元素——正是本单要修的缺陷。

## 模块防火墙自检

- 跨 App import：仍只走 `apps.element_locator.api`（本变更不新增跨 App import）
- 写库收敛：`device_inspector/api.py`（本模块）与 `element_locator/api_snapshot.py`（对方 api 层），无越层写
- 前端不直连数据库：不涉及
- HTTP / 端点 / 信封：端点路径与响应形状不变（仅新增一个可选请求字段）
- 迁移：零

## Risks / Trade-offs

- [旧版前端仍发 `aliases`] → 后端两条通道都在，行为不回归；新版前端只发 `element_aliases`
- [下标与元素顺序漂移] → `element_ids`（已存在）与 `element_aliases` 都必须相对同一份 `dump_json.elements`；测试用同名 rid 的两个元素显式断言
- [AI 工具受影响] → 不触碰其入参路径；既有 `aliases` 用例由回归测试覆盖（新增测试不动它）

## Migration Plan

1. 后端：`save_snapshot_to_elements` 加 `element_aliases`；`views.save_elements` 透传
2. 前端：`store.saveToElements` 组装 `element_aliases`（不再发 `aliases`）
3. 测试：新增集成用例（同名 rid 两元素各自保名 + 只勾选其一时的下标正确性）
4. 真机：造一个同 rid 快照（或直接用设备抓），两行分别重命名 → 保存 → 回看核对
5. 门禁：`manage.py check` + `ruff` + `pytest` + `lint:styles` + `vite build` + `vitest`
6. 回滚：`git revert`；无数据迁移（已写入的别名不回滚）

## Open Questions

（无）
