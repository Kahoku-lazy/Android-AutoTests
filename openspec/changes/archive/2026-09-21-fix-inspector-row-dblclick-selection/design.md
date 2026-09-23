## Context

- 失效链路（读码 + 受控实验）：数据格 → `pointerdown` → `useTableDragScroll.onTablePointerDown` → `el.setPointerCapture`（捕获 `.el-scrollbar__wrap`）→ 随后的 `click` / `dblclick` 被重定向到捕获元素 → EP `tr` 上的 `onDblclick`（`element-plus/.../table-body/render-helper.mjs:41` → `events-helper.mjs:12-25` 的 `table.emit('row-dblclick', …)`）收不到事件 → `StructureAnalysisPanel.onRowDblClick` 不执行 → `store.selected` 不变 → 无红框。
- 受控实验证据（同一页面、同一元素、只改 `setPointerCapture`）：捕获生效时 dblclick 目标为 `el-scrollbar__wrap`、选中 0 行、处理函数 0 次触发；页面级禁用捕获后 dblclick 目标为 `sap-label-hit`、选中 1 行、处理函数 1 次触发。
- 交叉印证：单击「元素名称」可进改名（该格有 `@pointerdown.stop`，composable 未运行）→ 未捕获的格子上手势正常。
- 结论：这不是检查器的判定逻辑问题，而是**共享拖拽件的副作用**；任何依赖表格行 `click` / `dblclick` 的页面都会同样失灵（当前 device-pool 未使用行事件，故只有检查器可见）。
- 规格侧：`device-inspector-page` 已有该要求，无需 delta。

## Goals / Non-Goals

**Goals:**

- 数据格的双击手势恢复（选中 + 手机画面红框）
- 拖拽平移在拖拽被激活后仍然跟手（含指针移出窗口）
- 两个消费方（`/inspector` 与 `/devices`）都真机验收

**Non-Goals:**

- 不改拖拽的激活阈值（长按 180ms / 横移 6px）、光标、拖动后吞掉一次 click 的既有语义
- 不改检查器的双击判定与红框绘制
- 不改 `INTERACTIVE` 排除清单

## Decisions

**D1 把 `setPointerCapture` 延后到拖拽激活（`activatePan`）**
激活前不捕获 → 数据格的 `click` / `dblclick` 落到原目标，行事件恢复正常；激活后捕获 → 保留「拖动时指针移出窗口仍跟手」的既有收益。实现上把 `try { el.setPointerCapture(pointerId) }` 从 `onTablePointerDown` 移入 `activatePan`（此时 `pointerId` 已是模块内状态）。
备选：把数据格加进 `INTERACTIVE` 排除清单 → 否决：表格主体区域将无法拖拽平移（拖拽的初衷就是「在空白处按住拖动」），且需要枚举所有格子。
备选：让检查器自己在 `td` 上监听 `dblclick` → 否决：指针被捕获后事件根本不派发到 `td`，监听也收不到。
备选：在 `pointerup` 时显式 `releasePointerCapture` → 否决：双击的第二次 `pointerdown` 会再次捕获，`dblclick` 仍在捕获状态下派发，问题不解决。

**D2 不引入「仅鼠标不捕获」之类的分支**
理由：捕获的副作用与指针类型无关（触控同样重定向），按指针类型分支只会把问题留一半；延后捕获对所有指针类型一致有效。

## 模块防火墙自检

- 跨 App import：零新增（只改共享件内部实现）
- 跨 App import service/runner/consumer/state_machine：不涉及
- 写库收敛 api.py：不涉及（无后端改动）
- 前端不直连数据库：不涉及
- HTTP 出口：不变（本变更不发任何请求）
- 共享层：**本变更就是改共享件**；改动仅位置调整，不改导出签名与语义（`tableWrapRef` / `onTablePointerDown` 返回结构不变）
- 后端 / 端点 / 路由 / 迁移：零改动

## Risks / Trade-offs

- [延后捕获后，长按等待期内指针移出窗口可能丢 move] → move/up 监听挂在 `window` 上（既有实现），窗口内外的移动都能收到；真机拖动验证 scrollLeft 变化
- [device-pool 的拖拽回归] → 同一共享件被两处消费；验收清单含 `/devices` 真机拖拽（若该页当前无横向溢出则记录该事实并说明无法在该页复现）
- [拖动误触行选中] → 既有逻辑在 `didPan` 时吞掉一次 `click`，本变更不动它；真机复核拖动后未产生选中

## Migration Plan

1. 调整 `useTableDragScroll.ts` 的捕获时机
2. 真机：`/inspector` 双击数据格 → 选中 + 红框；单击不选中；`/devices` 拖拽平移仍生效
3. 门禁：`npm run lint:styles`、`npx vite build`、既有 vitest 全量（共享件被多处引用）
4. 回滚：单文件 `git revert`

## Open Questions

（无）
