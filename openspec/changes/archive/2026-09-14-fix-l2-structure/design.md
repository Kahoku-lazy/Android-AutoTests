## Context

- 现状与问题量化见 `proposal.md`。本设计只写方案需要的约束：
- `style.css` 的 `.doc-page { display:flex; flex-direction:column }` 与 App.vue 的 `.main-content__body :deep(.doc-page) { flex:1; min-height:0; height:auto; overflow:visible }`（选择器权重 3）会**覆盖模块 scoped 的** `.doc-page[data-v]{ height:100% }`（权重 2）——因此 D 类页面迁移后，其私有根里的 `height:100%` 会成为死声明。
- `.doc-page--fixed .doc-body { padding: var(--app-space-md) 18px 28px; overflow-y:auto }`（全局，权重 2）与模块 scoped 的覆盖（权重 2 + 后加载）共存；迁移后每页最终内边距必须实测复核（P8）。
- `WorkbenchHeader` 的「几何用 `!important`、颜色交还主题层」分工已在 `fix-l2-page-region` 定型，本变更不动它。
- C 类（report 详情）是**策略①**（`.main-content__body` 整页滚），A 类是**策略②**（`.doc-body` 内滚）——换成同一个页头组件后两者的滚动分工仍然不同。

## Goals / Non-Goals

**Goals:**

- L2 结构单一化：页面根骨架一种、页头共享件一个、水平内边距一个值。
- 清理 L2 死代码，并顺带清掉**因本次迁移而产生**的死声明。
- 观感与行为零回退（点阵底纹、分隔线、树/表格布局、滚动出口）。

**Non-Goals:**

- 不统一滚动策略：C 类仍为策略①，页头随内容滚动（与 A 类不同），本次只统一零件。
- 不合并 `workflow/index.vue` 的 `.wb-body`（画布布局差异大，属 L3 容器，另行评估）。
- 不改点阵纹理归属（dashboard/device-inspector 的 `.doc-page` 点阵仍在），不处理页头下方的多余 `border-top`。
- 不新增设计令牌；不动 L0/L1 骨架；不动 API/路由/后端。

## Decisions

**D1 P5 迁移方式：根加骨架类、主体改 `.doc-body`、模块规则改由根类限定作用域。**
例：`<div class="project-workspace wb-shell">` → `<div class="doc-page doc-page--fixed wb-shell project-workspace">`；`<div class="project-workspace__main">` → `<div class="doc-body">`；模块样式 `.project-workspace__main { … }` → `.project-workspace .doc-body { … }`。
这样模块规则带 `[data-v]` 后选择器权重为 3，**确定性地**压过全局 `.doc-page--fixed .doc-body`（权重 2），不依赖 CSS 加载顺序；与 `dashboard` 的 `.device-workbench .doc-body` 完全同构。
备选：(a) 彻底删私有类并把样式改写成 `.project-workspace .doc-body`——diff 更大，且与 `dashboard` 根（`doc-page doc-page--fixed wb-shell device-workbench`）既有写法不一致；(b) 只给根加类、主体不动——会出现「两个主体容器语义」，违反本变更目标。
理由：私有类保留即保留全部既有样式钩子，迁移风险最小；与既有 A 类页面完全同构。

**D2 迁移后删除因迁移产生的死声明。**
私有根规则里的 `display:flex` / `flex-direction:column` / `height:100%` / `min-height:0` 与骨架重复，且 `height:100%` 会被 App.vue 的 `:deep(.doc-page)` 覆盖；迁移时一并删除，只保留非骨架职责的声明（背景、边框、溢出、`overflow:hidden` 等）。
理由：AGENTS.md「只清理自己造成的混乱」——这些声明由本次迁移变为死代码。

**D3 P6 图标：三个详情页统一用已登记的 `file-bar-chart`**（与列表页同族），标题沿用现有文案（任务报告 / 测试执行报告 / 用例细分），`subtitle` 沿用现有动态串。
备选：每页配不同图标（\`clipboard-list\` / \`table\` 等）——`table` 未登记在 lucide 子集，会触发 lucide 告警，收益低。

**D4 P7 `mark` 清理范围：只删 `mark` prop、其默认值与模板 `v-else` emoji 分支。**
实施期核实：`.soft-icon*` 家族（`style.css:56-102`，8 组规则）在删除该分支后确实全仓无消费方，但它位于 **L0 全局段**且是通用工具类，按 `frontend/AGENTS.md` L0「既有类留在原处不动」的约定**本次不删**，仅作为无消费方登记（单独评估属 L0 清理，不在本变更范围）。
理由：核实过 16 个 `WorkbenchHeader` 用法全部传 `icon`，`mark` 零消费。

**D5 P7 `PAGE_HEADER`：改为被消费，而非删除。**
给 report-generator 的 `PAGE_HEADER` 补 `icon: 'file-bar-chart'` 与 `iconGradient`，列表页模板改读常量。
备选：删常量、保留模板硬编码——但硬编码标题/图标违反 frontend 规范「禁止魔法字符串」，且与 dashboard / device-pool / ai-assistant 三模块的「常量 → 模板」模式不一致。

**D6 P8 基准值 `var(--app-space-lg)`（24px），不新增专用令牌。**
落点：`style.css` 全局 `--fixed .doc-body` 的 `18px`、`report-generator/index.vue` 的 `20px`、`ai-assistant/index.style.css` 缺少的左右内边距、`device-inspector/index.vue` 的 `28px`、`case-manager/CaseFileSheet.vue` 的 `12px`；页头 `padding: var(--app-space-sm) var(--app-space-lg)` 不动。
备选：新增 `--l2-inline-inset` 令牌——语义更明确，但需同步 `tokens.css` / `DESIGN_SYSTEM.md` / doodle-craft 三处，且当前与 `--app-space-lg` 同值，属过度设计。

## 模块防火墙自检

- **跨 App import**：无。本变更纯前端模板/样式/共享件，未新增任何 `apps/` 间依赖。
- **禁止跨 App import service/runner/consumer/state_machine**：不涉及。
- **所有 INSERT/UPDATE/DELETE 收敛到 api.py**：不涉及，本变更无写库、无 HTTP 调用改动。
- **前端不直连数据库**：不涉及。
- **仪表盘不做写操作**：`dashboard` 仅受 P8 内边距影响，未新增写操作。
- 结论：未引入新的跨模块依赖，无需走 `api.py`。

## Risks / Trade-offs

- [7 页迁移后私有根的 `height:100%` 被删，若某页实际依赖它撑高会高度塌陷] → 逐页浏览器实测页面根高度是否等于视口高、主体是否仍可滚；不通过则改为在模块作用域显式补高。
- [主体元素同时挂 `.doc-body` 与私有 `__body` 类后，全局 `.doc-body` 与私有规则的声明可能互相打架] → 模块 scoped 的 `[data-v]` 使其权重高于全局；迁移后必须**实测每页最终 padding**，并统一到 24px（P8）。
- [P6 换页头后，`PageHeader` 原有的 `margin-bottom: var(--app-space-lg)` 消失，详情页首屏内容上移] → 实测三页首屏间距；必要时在详情页作用域给 `.doc-body` 补 padding-top。
- [P7 删 `mark` 后若有调用方依赖 emoji 回退会渲染空白] → 变更前已 grep 确认 16 处全部传 `icon`；变更后再次 grep 断言无 `mark` 传值。
- [P8 把全局 `--fixed .doc-body` 从 18px 改 24px 会同时影响未单独覆盖的页面（`AgentDetail` / `SkillViewerPage`）] → 这正是目标（左边缘对齐）；实测两页与页头对齐即可。
- [D 类页面迁移后视觉回退（点阵/分隔线/表格布局）] → 逐页对比迁移前后的关键几何（树面板宽度、表格容器宽度、页头底边）。

## Open Questions

（无）
