## Context

`libraryStore.ts:392-427` 的空覆盖保护分支有三态：`skipEmptyOverwrite` 直接 return（自动保存 / 切页）、`confirmEmptyOverwrite` 弹窗询问、两者都没有时默认不覆盖。UI 依赖只在第二态（`:412` 的 `ElMessageBox.confirm`），且 `ElMessageBox` 在该文件内**仅此一处**使用（实测导入行 `:6`）。

弹层配置实测：显式 `:close-on-click-modal="false"` 共 8 处（`ProjectList` / `PrototypeList` / `ProjectTree` / `CaseFileSheet` / `LocatorTree` / `NetworkConnectDialog` / `DisconnectDialog` / `KnowledgeImportDialog`），`destroy-on-close` 1 处（`EvaluatorTab` 试卷编辑器），其余依赖默认。

## Goals / Non-Goals

**Goals:**

- 给弹层关闭策略一个可验收判据，并让 19 处配置全部符合它
- 让 `libraryStore` 完全脱离 Element Plus / DOM

**Non-Goals:**

- 不把 19 处弹层统一成同一个值（判据本身就是「按内容性质二分」）
- 不禁止视图层与 composable 使用 `ElMessage` / `ElMessageBox`（那是它们的职责；本变更只约束 store）
- 不改任何弹层的字段、布局与确认文案
- 不给非「需重置本地状态」的弹层加 `destroy-on-close`

## Decisions

**D1 · 关闭策略的判据取「是否含输入」，而不是「统一为 false」**

统一为 `false` 会让预览类弹层变得难以关闭（点遮罩无反应），是 UX 倒退；统一为默认又会让表单类弹层误触丢失输入。按内容性质二分既消除了随意性，也不牺牲任一侧。危险确认归入「需显式决定」一侧（`DisconnectDialog` 已是 `false`，符合判据）。

**D2 · `destroy-on-close` 只写判据不新增用法**

它解决的是「弹层内容持有本地状态、二次打开需重置」。实测只有试卷编辑器需要（`editingBank` / `bankForm` 由父级状态驱动但内容复杂）。其余弹层要么每次打开由调用方显式重置（如 `openDialog` 重置表单），要么是只读内容，加它只会白白增加重建开销。

**D3 · store 解耦用「回调参数」而非「返回信号 + 重试」**

备选一是 store 返回 `{ needsConfirm: true }` 让调用方重试：需要调用方在重试时重建 payload，且把「是否空图」的判断散到两处。备选二是 store 抛专用错误：控制流靠异常表达，可读性差。回调参数只把**弹窗实现**外移，条件判断仍留在 store 一处，diff 最小且语义直白。

**D4 · 回调签名带上 `remoteNodes`**

原文案含远程节点数（`服务器上已有 N 个节点…`），带上该参数才能逐字保留文案，也避免调用方为了拿这个数再查一次远端。

## 模块防火墙自检

- 跨 App import：不涉及。只改 `frontend/src` 内部
- 禁止跨 App import service / runner / consumer / state_machine：不涉及
- 所有 INSERT / UPDATE / DELETE 收敛到各 App 的 api.py：不涉及，无后端写操作
- 前端不直连数据库；仪表盘不做写操作：不涉及，不改任何 `api.ts` / HTTP 调用
- 新增跨模块依赖：无（改动方向是**减少**依赖：store 不再依赖 element-plus）

## Risks / Trade-offs

- [`confirmEmptyOverwrite` 由布尔变为函数后，若某调用方仍传布尔值会类型不匹配] → 调用方只有 `workflow/index.vue` 一处，一并改；`vue-tsc` 会拦住类型不符
- [store 移除 `ElMessageBox` 后，取消语义改由回调返回 `false` 表达] → 回调实现里用 `try/catch` 包裹 `ElMessageBox.confirm` 并返回 `false`，与原 `catch { return }` 等价
- [给 4 个弹层加 `false` 后，习惯点遮罩关闭的用户会觉得「关不掉」] → 这正是意图（防误触丢失输入）；ESC 与取消按钮仍可关，浏览器核验项已登记
- [判据「含输入」在边界情形（只读表格里带内联编辑）有解释空间] → 在 spec 场景中列举了当前 19 处各归哪一侧，后续新弹层按同一列举判断

## Migration Plan

- 无数据迁移；回滚为 revert 本变更提交
- 顺序：先改 store + 调用方（②）→ 再补 4 处弹层属性（①）→ `vue-tsc` → 速查同步 → 归档
