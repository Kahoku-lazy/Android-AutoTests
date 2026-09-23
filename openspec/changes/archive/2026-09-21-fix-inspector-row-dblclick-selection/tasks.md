## 1. 延后指针捕获

- [x] 1.1 `frontend/src/shared/composables/useTableDragScroll.ts`：`onTablePointerDown` 不再捕获指针；新增 `capturePointer(el)` 并只在 `onMove` 真正开始横移（`panReady` 之后）时调用；验证：`setPointerCapture` 唯一调用点在 `capturePointer` 内（第 71 行），由 `onMove`（第 90 行）触发
      **实施中修正（重要）**：首版按 design D1 把捕获放进 `activatePan`——但 `activatePan` 会被「长按 180ms 但未移动」触发，慢一点的双击仍在捕获态下完成，实测双击选中依旧为 0。改为「只在真实横移时捕获」后通过。design D1 的措辞已按此更新。

## 2. 真机验收（两个消费方）

- [x] 2.1 `/inspector`（`temps/inspector-dblclick-final.mjs`）：单击「标识」→ 选中行 0；双击第 2 行「标识」→ 选中行 **1** 且画布像素哈希 `2305192828 → 477370957`（红框确实画出）。第 1 行元素坐标为 0×0，规格要求此类元素 MUST NOT 画出可见填充 → 未画属正确行为
- [x] 2.2 同脚本：双击「元素名称」→ 出现重命名输入框 1 个且原选中行不变；双击「缩略图」→ 放大弹窗出现 1 个且选中行不变
- [x] 2.3 拖拽平移：`/inspector` 实测从数据格起手拖动 `scrollLeft 0 → 60 → 140`，松手后 800ms 仍为 **140**（未回弹）；`/devices` 在 820px 视口下 `.device-table-wrapper` 的 `scrollWidth == clientWidth == 512`——**该页当前无法产生横向溢出**，故无法在该页复现拖拽（如实记录，未伪造读数）；两页 `pageerror` 均为 0

## 3. 门禁与归档

- [x] 3.1 `openspec validate fix-inspector-row-dblclick-selection --strict`；验证：valid（`skip_specs` 生效）
- [x] 3.2 `npm run lint:styles`；验证：`LINT_EXIT=0`
- [x] 3.3 `npx vite build`；验证：退出码 0，`✓ built in 3m 23s`
- [x] 3.4 `npx vitest run`（全量）；验证：**217 passed / 17 failed（5 文件）**，17 处失败全部与本次改动无关——`tests/device-pool/p0/api.spec.ts` 多例断言期望无尾斜杠而实现已有尾斜杠（他人已提交的 `/api` 尾斜杠统一改造未同步旧断言）、`tests/device-pool/p1/DevicePoolView.logic.spec.ts` 分页期望（`expected 3 to be 2`）、`tests/dashboard/p1/ModuleNavigator.spec.ts` 导入已删除的 `ModuleNavigator.vue`（他人重构）；`tests/device-inspector` 单独运行 **3/3 通过**，`useTableDragScroll` 相关无失败
- [x] 3.5 与 `fix-saved-page-shot-basis` 互相引用；验证：该单 tasks 2.1 的运行时验证以本单修好的选择手势为前提——本单已在 `/inspector` 复现「双击选中 + 画框」并经该单复验（`redrawOnSelect: true` / `redrawOnClear: true`）
