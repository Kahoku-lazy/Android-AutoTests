## Context

侧栏当前的线型由 `tokens.css` 的共享组件令牌 `--comp-sidebar-dash`（`2.5px dashed var(--ink)`）统一供给，`.sidebar` 只是把它转存为 `--sidebar-dash` 后消费六处描边。仪表盘章节板 `.doc-section--board` 则在模块样式里把全局 `.doc-section` 的墨色实线覆写成虚线，并叠加模块色硬阴影与微倾。

本仓已有一条前置决定：登录页是**唯一**保留虚线的页面，登录页已用作用域令牌 `--login-line: dashed` 自持线型，且 `frontend-l0-design-tokens` 要求线型由消费边界自持、MUST NOT 借用 `--comp-*`。侧栏的共享线型令牌因此不再符合该口径。

## Goals / Non-Goals

**Goals:**

- 侧栏六处描边（外右分隔、品牌区底线、激活项描边、子导航左引导线、报尾顶线、用户卡描边）统一改为 2.5px 墨色实线，线型由侧栏自持。
- 仪表盘四个章节外壳恢复全局 `.doc-section` 的墨色实线；章节头与子标题分隔线改实线。
- KPI 卡 / 智能体卡 / 趋势 `AppCard` 的虚线皮肤零改动。

**Non-Goals:**

- 不改 KPI 卡、AppCard、SketchCard、DoodleNote 等共享卡壳的线型。
- 不改仪表盘页脚（`dashboard__footer`）与活动时间线的行分隔线——它们是页脚条 / 列表分隔，不属于本次「侧栏 + 章节外壳」范围。
- 不改登录页视觉，也不改 Element Plus 弹窗 / 表格 / 输入框的线型。
- 不改路由、接口、数据模型。

## Decisions

### D1：侧栏线型改为作用域自持，删除共享令牌

在 `.sidebar` 内声明：

```css
--sidebar-line: solid;
--sidebar-border: var(--size-stroke-sketch) var(--sidebar-line) var(--ink);
```

六处描边改为 `var(--sidebar-border)`，并从 `tokens.css` 删除 `--comp-sidebar-dash`。

理由：与登录页 `--login-line` 同一模式，线型所有权落在真正决定的边界；共享令牌一旦被别处改写会静默带走侧栏。备选「保留令牌只把值改 solid」被否：令牌名仍写着 dash，且通用组件令牌按规范只登记配色，不持有线型。

### D2：章节板删除虚线覆写，回到全局实线

删除 `.doc-section--board` 的 `border` 声明，保留 `border-radius: 2px`、模块色硬阴影、内边距与微倾。

理由：`.doc-section` 与 `.doc-page--fixed .doc-section` 已声明 `2.5px solid var(--ink)`；章节板选择器带 scoped 属性后与前者同权重且样式更晚，正好覆写成虚线。删掉覆写即可单点继承全局实线，避免模块里再写一份「实线」字面量。备选「就地写 `2.5px solid`」被否：会把描边宽度/颜色复制成第二份真相源。

### D3：章节头与子标题分隔线只改线型

`.chapter-head` 的 `border-bottom` 与 `.subhead::after` 的 `border-bottom` 把 `dashed` 改为 `solid`，宽度、颜色与透明度沿用现值。

理由：这两条线在章节外壳内部，若不改会留下「外壳实线、标题下仍是虚线」的割裂；它们是仪表盘局部装饰，不跨边界，不需要新增令牌。

### D4：卡片虚线保持原样

`KpiCard.vue`、`workbench-theme.css` 的 `.ac-card` 等一个字符都不动。`StatsAppCard` 是 `KpiCard` 的薄包装，因此「在线设备 / 累计用量」等卡片继续虚线；这也让本变更的影响面被 CSS 选择器边界天然限制住。

## 模块防火墙自检

- 不新增跨 App import；纯前端样式变更。
- 不触碰 INSERT/UPDATE/DELETE；仪表盘仍为只读展示。
- 不新增接口、不新增前端直连数据库路径。
- 不新增跨模块依赖；侧栏令牌只在 `shared/components/AppSidebar.style.css` 内声明与消费。

## Risks / Trade-offs

- [章节板描边宽度/颜色改为继承全局，可能与原虚线视觉的粗细观感不同] → 两者都是 2.5px 墨色，仅线型变化；验收时读取计算样式确认 width/style/color。
- [删除 `--comp-sidebar-dash` 后仍有残留引用] → 全仓检索 `comp-sidebar-dash` / `sidebar-dash`，并在 `npm run lint:styles` 与 `vue-tsc` 后再检索一次。
- [登录页被共享令牌变化波及] → 登录页早已改用 `--login-line`，本变更不改 `LoginView.style.css` 的任何声明。
- [需求方后续希望页脚也改实线] → 页脚不在本次范围；若需要，按同一模式只改 `.dashboard__footer` 一处。
