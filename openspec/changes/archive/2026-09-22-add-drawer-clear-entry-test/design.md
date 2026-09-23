## Context

- 生效要求 `openspec/specs/device-inspector-page/spec.md`「快照删除需二次确认」在本轮新增了「一键清空需二次确认」「确认后清空只调一次端点」「取消清空不删除」「无快照时清空不可用」四个场景。
- 落地代码：`frontend/src/modules/device-inspector/components/SnapshotListDrawer.vue`（`onClearAll` 走 `ElMessageBox.confirm`，按键 `:disabled="!store.snapshots.length"`）；`store.clearSnapshots()` 已有用例覆盖。
- 单测环境（`frontend/vite.config.js` 的 `isTest` 分支）不注册 Element Plus 按需组件，`el-*` 不会被解析；本仓既有做法是用 stub 替身（见 `tests/ai-assistant/p0/ToolboxPanel-tool-debug.spec.ts`）。

## Goals / Non-Goals

**Goals:**

- 用自动化用例锁住抽屉「一键清空」的三条行为：空态禁用、确认后只调一次端点、取消不发请求。

**Non-Goals:**

- 不改产品代码、不改规格、不引入浏览器/e2e 层（真实点击仍属人工验收）。
- 不为样式或文案排版加断言。

## Decisions

**D1 用 `el-button` 替身显式模拟「禁用不派发 click」。** 若让 `el-button` 保持未解析状态，它会按原生元素渲染，jsdom 下对 `disabled` 元素的 `dispatchEvent` 仍会触发监听器 —— 那样「禁用时点击不发请求」这条场景就测不出来（测的是 jsdom 而非本仓代码）。替身 `<button :disabled="disabled" @click="disabled ? null : $emit('click')">` 同时模拟了 EP 的两种行为。

**D2 用 `vi.hoisted` 暴露确认框替身。** `ElMessageBox` 与 `ElMessage` 同模块导出，`vi.mock` 工厂被提升，必须经 `vi.hoisted` 共享 mock 句柄（本仓既有范式）。

**D3 只加用例，不动产品代码。** 若用例暴露真实缺陷，另开单修；本单范围就是补验证。

## 模块防火墙自检

- **前端 HTTP 出口**：用例 mock `api.ts`，不新增调用。
- **产品代码**：零改动。
- **规格**：零改动（无 delta）。

## Risks / Trade-offs

- [替身与真实 Element Plus 行为存在差异] → 替身只模拟与本场景相关的两种行为（禁用不派发、正常派发）；真实渲染差异属 e2e 层，已在上一单记为人工验收项。
