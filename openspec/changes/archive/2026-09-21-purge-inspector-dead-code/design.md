## Context

- **目标模块**：`frontend/src/modules/device-inspector/`（无单测，`frontend/tests/README.md` 标注“未开始”）。
- **判定口径（本设计的唯一判据）**：对每个候选删除项在全仓（排除 `node_modules` / `dist`）检索其标识符与类名，命中仅剩“声明处自身 + `openspec/` 历史归档文本”即判为零消费。之所以用全仓检索而非构建：Vue 模板访问不存在的 store 键不会在构建期报错，`typecheck` 也不覆盖模板里的 store 键。
- **live spec 约束**：`device-inspector-page`「元素表列宽与间距集中登记」只要求**列宽与表格最小宽**登记在模块 `constants.ts`；`frontend-l4-data-surface`「Fixed page size still comes from module constants」只要求 `PAGE_SIZE_OPTIONS` 与默认行数**声明在** `constants.ts`。二者均未要求 `TABLE_HEADER_HEIGHT_PX` / `TABLE_ROW_HEIGHT_PX`。
- **范围调整（评审后）**：`snapshotTotal` 改由 `fix-inspector-state-fidelity` 消费（快照总数是真实信息，不是死状态）；`ScreenshotView.vue` 的 watcher 合并改由 `fix-saved-page-shot-basis` 承担。因此本变更不再触及 `ScreenshotView.vue`。
- **文件稳定性**：模块自 2026-09-21 16:12 起未再变化（`align-inspector-spec-drift` 之后），tasks 仍一律**锚定符号**（函数名 / 选择器 / 属性名），不锚定行号。
- 动机与范围边界见 `proposal.md`（Why / What Changes / 本变更范围的两处调整），此处不重复。

## Goals / Non-Goals

**Goals:**

- 把模块内剩下的“零消费声明 / 逐条死 CSS / 无效 CSS 声明 / 不可达分支 / 名实不符导出”归零
- 每条删除都能被一条静态命令复验（删除后命中数 0）
- 零可观察行为变化：几何、配色、文案、请求次数与时机均不变

**Non-Goals:**

- 不改页面布局、样式几何与令牌取值；不动 `tokens.css` 与 `shared/styles/*`
- 不改后端、端点契约、路由、依赖；不新增/删除请求
- 不删除 `snapshotTotal`（改由 `fix-inspector-state-fidelity` 消费）
- 不合并 `ScreenshotView.vue` 的 watcher（改由 `fix-saved-page-shot-basis` 承担）
- 不解决任何行为缺陷（`alias` 显示 / 错误原因 / 截图基准 / 悬空媒体）——各有专单
- 不为该模块补单测（由 `fix-inspector-state-fidelity` 首次补齐）

## Decisions

**D1 删除 `constants.ts` 的 `TABLE_HEADER_HEIGHT_PX` / `TABLE_ROW_HEIGHT_PX`**
理由：模块内 0 引用（唯一消费者 device-pool 用自己的 `device-pool/constants.ts` 同名常量）；live spec 未要求；注释“与设备管理页同口径”会让读者以为两处联动，实际是两份独立副本。
备选：保留作为“同口径”声明 → 否决：保留即复制品，反而制造“改一处忘另一处”的隐患，且 live 要求 `frontend-l2-page-region`「No L2 declaration without a consumer」明确「模块常量不得存在零 import 的导出」。
保留项（明确不动）：`PAGE_SIZE_OPTIONS` / `DEFAULT_PAGE_SIZE` / `ELEMENT_COLUMN_WIDTHS` / `TABLE_MIN_WIDTH_PX` / `EMPTY_TEXT`。

**D2 只清退 `analyzing`，`snapshotTotal` 转由另一单消费**
`analyzing`（声明 / 置位 / `return` 暴露，全仓无读点）整体删除；`devices` 有内部读点（`availableDevices`），只从 `return` 移除；`snapshotTotal` 保留——它是「快照总数」的载体，dev 库 309 条而抽屉只展示 100 条，`fix-inspector-state-fidelity` 会把它显示出来。
理由：死状态的判据是“写了没人读”，而 `snapshotTotal` 的问题是“有信息没人展示”——后者是缺陷，不是残留。
备选：一并删掉 `snapshotTotal` → 否决：等于确认“不告诉用户只展示了 100 条”，与 `fix-inspector-state-fidelity` 新增的「快照列表如实反映总量」直接冲突。

**D3 `KEY_DISABLED_MESSAGE` 去掉 `export`（保留常量本体）**
理由：该常量的注释声称“index.vue 与 CaptureForm.vue 共用”，但两处都改走 `store.notifyKeyUnavailable()`，全仓无人 import；文案唯一真相源的价值保留在模块内即可。
备选：常量与 `notifyKeyUnavailable` 一起内联掉 → 否决：文案会被压进函数体，失去“文案唯一登记处”的作用。

**D4 删除 `toggleCheck` 的 `row.__uid` 兜底**
理由：全仓 `__uid` 仅此 1 处出现，无任何产出方；行键的真实来源是 `_rowKey`（结构分析/已保存页面统一补 `d<下标>`）与 `_idx`。
备选：补一个 `__uid` 产出方 → 否决：当前无此语义需求。

**D5 删除两条逐条死 CSS**
`.no-signal--error .no-signal__title`（模板只有 `no-signal--idle`）、`.save-hint`（模板无该 class），均为全仓 0 引用。
理由：死 CSS 会让样式检索无法判断“哪条规则真的生效”。
备选：保留为未来错误态样式 → 否决：需要时再登记，不留半成品。

**D6 删除 `.no-signal__icon` 的 `font-size`，保留 `opacity`**
理由：该节点内的图标是 `<IconDevice :size="32" />`，渲染为 `<svg width="32" height="32">`（`shared/icons/index.ts` 的 `makeIcon`），字号不参与尺寸计算，该声明对渲染零作用。
备选：把字号意图改成给图标的 `:size` → 否决：那会**改变视觉尺寸**，超出本次“零观感变化”的范围。

**D7 `ScreenshotView.vue` watcher 合并：移出本变更，改由 `fix-saved-page-shot-basis` 承担**
理由：该单本来就要改 `ScreenshotView.vue` 的尺寸基准，且合并 watcher 的语义验证（选中→重绘+滚动；清空→重绘）与它的真机走查是同一次；两单同文件交叉会多付一次走查与一次冲突排查。
备选：留在本变更 → 否决：会把「纯删除」变成「语义重写」，与本变更 `skip_specs` 的定位不符。

**D8 `usePagination` 的 `options: PAGE_SIZE_OPTIONS` 传参保留，不进本变更**
理由：该参数确无运行时作用（调用方不消费 `PAGE_SIZE_OPTIONS` / `setPageSize`），但 live spec 要求 `PAGE_SIZE_OPTIONS` **仍须声明在 `constants.ts`**。若去掉这次传递，该常量会变成“规格要求存在、代码零消费”的导出，未来死代码扫描会再次把它判为死代码并可能误删，从而违反 spec。保留这一处传递 = “登记项 → 唯一分页实现”的显式接线。
备选：去掉传参并在 `constants.ts` 加注释说明“仅供登记” → 否决：注释挡不住扫描，接线才是硬证据；且去掉传参会让 `PAGE_SIZE_OPTIONS` 变成零 import 导出，直接违反 `frontend-l2-page-region`「No L2 declaration without a consumer」。

## 模块防火墙自检

- 跨 App import：**零新增、零改动**（本变更全部是前端模块内删除，不新增任何 import；`SaveToElementsDialog.vue` / `SavedPagePicker.vue` 既有的 `@/modules/element-locator/api` 引用本次不动）
- 跨 App import service/runner/consumer/state_machine：不涉及（纯前端）
- INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无后端改动、无写库路径变化）
- 前端不直连数据库 / 仪表盘只读：不涉及
- HTTP 出口：仍为各模块 `api.ts` → `@/shared/api-client`；本次请求数与时机不变（被删状态 `analyzing` 从未被任何请求逻辑读取）
- 共享层：不动 `shared/**`（`AppTable` / `EmptyState` / `ErrorState` / `usePagination` / `useTableDragScroll` 均不改）
- 令牌与样式：不动模块 `tokens.css` 与 `shared/styles/*`；被删 CSS 不引用任何令牌
- 后端 / 端点 / 路由 / 迁移：零改动

## Risks / Trade-offs

- [被删项其实被动态键消费（如模板字符串拼出的类名/键名）] → 判定用全仓静态检索而非仅 `frontend/src`；本次删除项均为字面量标识符与字面量 class，不含动态拼接（动态键 `nameOverrides[idx]`、`_rowKey` 不在删除范围）
- [去掉 `devices` 暴露后若有消费方被漏检] → Vue 模板访问不存在的 store 键**不会**在构建期报错，故以全仓检索为硬判据，并在 tasks 中设置“删除后复验命中数 0”的显式步骤
- [删 `analyzing` 误伤未来加载态] → 它当前无任何读点；若将来需要加载态，应在加 UI 的同时重新登记，而不是保留一个“看起来有加载态”的假信号
- [`store.ts` 与另两单同文件] → 本次只动 `analyzing` 声明、`return` 成员列表、`KEY_DISABLED_MESSAGE` 的 `export`、`__uid` 兜底；与错误分支 / `deleteSnapshot` / `viewSavedPage` 不同行，应用顺序无关
- [`constants.ts` 删除表头/行高常量后该口径知识在检查器内消失] → 该口径的 live 归属是设备管理页 `device-pool/constants.ts`；检查器确需时再按 spec 登记，不在本变更预留

## Migration Plan

1. 按 D1–D6 逐文件删除 → 每项删除后立即静态复验（命中数 0）
2. 门禁：`npm run lint:styles`（退出码 0）→ `npx vite build` → `npm run typecheck`（错误集合不新增）
3. 真机核查：`/inspector` 无快照空态渲染（图标/文案）、快照抽屉与保存弹窗正常渲染
4. 回滚：全部为删除，`git revert`（已提交）或 `git checkout -- <path>`（未提交）；无数据迁移、无部署顺序

## Open Questions

（无）
