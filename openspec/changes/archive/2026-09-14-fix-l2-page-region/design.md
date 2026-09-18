## Context

- L2 区域由两半组成：**页头区**（`WorkbenchHeader` 16 个文件 / 8 个模块；`PageHeader` 3 个文件）与**页面根区**（5 类根容器，共 21 个页面）。
- Doodle Craft 按钮皮肤分两层：**基础皮肤**在 `workbench-theme.css:48-79`（锚点 `.wb-shell` / `.workflow-workbench`），**变体色**在 `motion.css:5-32`（只写 Element Plus 自定义属性 `--el-button-bg-color` 等，不直接声明 `background`）。
- `WorkbenchHeader.vue:129-145` 自带一段 `!important` 兜底皮肤。`!important` 在**声明层面**压过一切非 `!important` 声明，与选择器权重无关——这是页头按钮语义色全部失效的根因；同一原因使 `wb-btn--*` 变体（其规则只有自定义属性）在页头内也不可见。
- `.wb-header` 定高 `var(--app-topbar-h)`（`tokens.css:334` = 96px，与 `.sidebar__header` 同高），无 `@media`、无 `overflow`；`.header-actions` 允许 `flex-wrap: wrap`；`z-index: 10` 落在 static 元素上。
- 主题作用域只认 `.wb-shell` / `.workflow-workbench`；`AppCard`/`AppTable` 的 `.ac-*` 覆盖因此只在带锚点的页面生效（`frontend/AGENTS.md` 已登记该口径）。
- 动机与范围见 `proposal.md`；行为契约见 `specs/frontend-l2-page-region/spec.md`。

## Goals / Non-Goals

**Goals:**

- 页头按钮的语义色与变体色恢复规范值，且皮肤色板仍只有主题层一个真相源。
- 页头内容在窄视口收敛（截断 / 不换行）而不侵入正文；页头层叠声明实际生效。
- 为 11 处缺失作用域的 L2 页面根补 `.wb-shell`，使同一模块的列表页与详情页共享组件外观一致。

**Non-Goals:**

- 不统一 L2 容器命名、不把 D 类私有根（`.project-list-page` 等）重构为 `.doc-page`/`.doc-body`。
- 不废弃或合并 `PageHeader`，不统一页头形态（两种零件并存维持现状）。
- 不处理点阵纹理（dashboard / device-inspector 的 `.doc-page` 点阵与 4 处私有主体点阵）、页头左内边距差异（18/20/24/28px）与 `ErrorState` 边距。
- 不修未使用的 `wb-btn--teal` / `--berry` / `--sky` 变体。
- 不改动 L0 纸面 / 滚动策略与 L1 主区骨架。

## Decisions

**D1 页头皮肤只保留几何，颜色交还主题层。**
`.wb-header :deep(.el-button)` 仅保留几何与无冲突属性（`border-radius`、`padding`、`font-weight`、`font-family`、`border-width: 2.5px`、`transition`、`box-shadow`），删除 `background` / `color` / `border`（简写）上的 `!important`；同时删除 `.wb-header :deep(.el-button:hover)` 的 `background: var(--app-highlight) !important`（否则 hover 仍会把 primary/danger 压成同一种黄），`:active` 的位移保留。
备选：(a) 保留 `!important` 并加 `:not()` 链排除类型按钮——不可读且随 EP 类名变化失效；(b) 把页头皮肤整体搬进 `workbench-theme.css`——与 doodle-craft「复制 `:deep()` 块」的既有做法冲突，且把几何与皮肤拆到两处。
理由：主题层不声明几何属性，故几何继续用 `!important` 无冲突；颜色一并交还后 primary/success/danger/默认各自回到规范值，色板真相源仍在主题层。
注意：`border-width: 2.5px !important` 必须保留，用于覆盖基础皮肤的 `border: 2px solid` 简写。

**D2 `wb-btn--*` 变体改为直接声明颜色属性。**
`motion.css` 的 `.wb-btn--sunset` 改为直接声明 `background` / `border-color` / `color`，不再只写 `--el-button-*` 自定义属性。
备选：保留自定义属性、删掉基础皮肤的 `background`——会连带改掉所有 `.wb-btn` 的默认皮肤，影响面更大。
理由：变体规则选择器权重（0,4,0）本就高于基础皮肤（0,3,0），直接声明即生效，且不影响其它按钮。

**D3 页头布局改为「文本单行收敛 + 动作区换行增高」。**
`height` → `min-height: var(--app-topbar-h, 96px)`；`.brand-title`/`.brand-sub` 加 `white-space: nowrap; overflow: hidden; text-overflow: ellipsis`；`.header-actions` **保持既有 `flex-wrap: wrap` 不变**。
备选：(a) 保留固定 96px + `overflow: hidden`——会静默裁掉动作按钮，比溢出更糟；(b) 把 `.header-actions` 改成 `flex-wrap: nowrap` + 按钮 `flex-shrink: 0`——实施期实测推翻：按钮不能省略号收缩，`nowrap` 只会把动作挤成**横向溢出**，而 `min-height` 永不触发，等于把纵向溢出换成横向溢出；(c) 文本也允许换行——长副标题会把常规宽度下的页头撑高，破坏与侧栏 header 的 96px 对齐。
理由：文本用省略号吸收，动作区换行后由 `min-height` 增高把正文下推；常规宽度严格 96px，窄屏才增高，且两种情况下都不覆盖正文（Playwright 实测：768px 下 workflow 六动作页头 96→134px、自身无溢出、正文下推）。

**D4 层叠：补 `position: relative` 让既有 `z-index: 10` 生效。**
备选：删除该 `z-index` 死声明。理由：保留作者意图（页头应压在正文之上），`position: relative` 无布局副作用；删除会丢掉未来吸顶 / 叠层阴影的锚点。

**D5 主题作用域：为 11 处页面根显式补 `wb-shell`。**
备选：(a) 把锚点上移到 `.main-content__body`（1 处覆盖全站，但改变 `.wb-shell`「工作台外壳」的既有语义，并把主题带到登录页 / 404）；(b) 把 D 类私有根类名加进 `workbench-theme.css` 选择器（让共享主题依赖模块私有命名，违反「禁止自造同类容器命名」）。
理由：显式补锚点与 `dashboard`（`.doc-page doc-page--fixed wb-shell device-workbench`）的既有写法一致，行为面最小。

**D6 `workflow/index.vue` 不补 `wb-shell`。**
其根已带 `.workflow-workbench`，该锚点已在主题层登记（`workbench-theme.css:5-6`），属等价作用域；`workflow/PrototypeList.vue` 的 `.proto-list-page` 无此锚点，需补。

## 模块防火墙自检

本变更纯前端样式与类名，逐条确认：

- **跨 App import**：无。未新增任何 `apps/` 之间的 import。
- **禁止跨 App import service/runner/consumer/state_machine**：不涉及。
- **所有 INSERT/UPDATE/DELETE 收敛到 api.py**：不涉及。本变更无写库、无 HTTP 调用改动。
- **前端不直连数据库**：不涉及。
- **仪表盘不做写操作**：`dashboard/index.vue` 仅改页头按钮呈现，未新增写操作。
- 结论：未引入新的跨模块依赖，无需走 `api.py`。

## Risks / Trade-offs

- [补 `.wb-shell` 会连带启用 `.wb-shell * { box-sizing: border-box }` 与 `.wb-shell { font-family: var(--ac-font); color: var(--ac-ink) }`，可能让 case-manager / element-locator 既有布局出现尺寸位移] → 对这两个模块的 6 个页面逐页目视回归（表格列宽、树面板宽度、横向滚动、文字换行）；若出现位移，改为在该页面根补最小作用域而不是整体回退。
- [`motion.css` 与并行变更 `align-frontend-motion` 同文件] → 只改 `.wb-btn--*` 块、不动 `.fade-slide-*`；两条规则互不重叠，合并顺序不影响结果。
- [页头改 `min-height` 后，极端窄视口下页头增高会与固定 96px 的侧栏 header 不再对齐] → 刻意取舍：spec 用「≥1280px 必须对齐」守住常规宽度，窄屏只要求不覆盖正文。
- [`.header-actions` 改 `nowrap` + 按钮 `flex-shrink: 0`，极窄宽度下动作区可能横向溢出] → 先由 `.brand-text`（`min-width: 0`）压缩到 0 吸收；spec 验证档位限定在 768px 以上。
- [删除颜色类 `!important` 后，若某页头按钮不在主题锚点内会退回 EP 默认外观] → 本变更让全部 16 个 `WorkbenchHeader` 消费方的页面根都带锚点，并在 tasks 中加一条「消费方 ↔ 锚点」清单断言。
- [`motion.css` 变体改直接声明颜色后，若将来有人重新加回基础皮肤的显式 `background`，变体仍会被压住] → 在 `motion.css` 变体块补一句注释说明「变体必须直接声明颜色，不能只依赖 EP 自定义属性」。

## Open Questions

- 未使用的 `wb-btn--teal` / `--berry` / `--sky` 三个变体目前同样被基础皮肤的显式 `background` 覆盖而失效；本次只修实际使用的 `--sunset`。这三个是保留待用还是删除，可在后续变更决定，不影响本变更的方案与任务拆分。
