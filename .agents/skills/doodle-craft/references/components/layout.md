# 布局类组件规格 — 页头 / 面包屑 / 侧栏 / 分区 / 标签页

维度 × 实际规格。**以代码为准**：`frontend/src/shared/components/**` 与 `frontend/src/shared/styles/workbench-theme.css`。令牌值见 [../tokens.md](../tokens.md)。

> **作用域警示**：`.ac-tabs` 等涂鸦皮肤**只在 `.wb-shell`（或 `.workflow-workbench`）内生效**。页面根忘带主题作用域 → 直接退化成 Element Plus 默认皮肤。
> **读法**：标「未覆盖」= 走 EP 出厂值。

## 1. WorkbenchHeader 页头（L2 唯一页头）

- **结构**：`header.wb-header` › `.wb-header__row` › `.brand`（图标块 + 标题 + 副标题）+ `.header-actions`
- **几何**：高 `min-height: --app-topbar-h`（96px，与侧栏品牌区底边对齐）、内边距 `--app-space-sm --app-space-lg`、底 `--paper`（与纸面同色）、下框 `2.5px solid var(--ink)`、`position: relative` + `z-index: --z-header`（10）
- **图标块** `.brand-mark`：40×40、圆角 `8px 16px 6px 14px`、框 2.5px 墨、微倾 `-2deg`、底色由 `iconGradient` 注入（默认 `--c-workflow` → `--comp-wb-icon-gradient-end`）
- **标题** `--app-size-2xl` / 700 / `--app-font-display` / 微倾 `-0.5deg` / 单行省略；**副标题** `--app-size-xs` / `--app-text-secondary` / 单行省略
- **动作区** `margin-left: auto`；放不下就换行、由 `min-height` 增高把正文下推，**不许溢出压正文**
- 按钮语义色必须保留（primary / success / danger / 主题变体各自底色），**不得**把页头按钮压成统一白底
- 一个页面只有一个页头；返回与面包屑放 `.doc-body` 顶部（见下），不放页头

## 2. WorkbenchCrumbs 面包屑（L2+ 子页导航）

- **渲染位置**：子页 `.doc-body` 的**顶部**，加载 / 错误 / 空 / 有数据各态都可见；**不得**放进 `.wb-header`
- **返回芯片** `.wb-crumbs__back`：框 `2px solid --comp-crumb-ink`、底白、圆角 `--comp-sheet-radius`（`2px 6px 2px 4px`）、硬影 `--comp-crumb-back-shadow`；hover `translate(-1,-1)`、active `translate(1,1)` + 影收窄
- **祖先链**：可点，波浪下划线 `--comp-crumb-wave`；**当前项**：马克笔底纹 `--comp-crumb-marker` + `aria-current="page"` 不可点
- 排版 `--app-size-xs` / 800；分隔符 `／` 取 `--comp-crumb-muted`；长文案截断（链接 220px、当前项 260px）
- props：`items`（`{label, to?}`）/ `backTo` / `backLabel`（默认「返回」）；`aria-label="面包屑"`
- **禁止**用正文里的 `.back-btn` 自建第二套回退导航

## 3. AppSidebar 侧栏（L1，模块不许改）

- **底色** `--paper`；**宽度** `var(--side-w)`：默认 **260px**，可拖拽 180–360，折叠 64px（`228px` 只是初始化前的兜底值）
- **品牌区**：高 `--app-topbar-h`（96px）、底部虚线分隔；品牌块 28×28、2.5px 墨框、黄底、青绿硬影
- **导航项**：`min-height: 42px`、内边距 `10px 12px`、圆角 `2px`、框 `2.5px solid transparent`、字 `--app-size-sm` / 700
- **激活项**：底 `--app-highlight`、字 `--ink`、字重 800、`2.5px` 虚线上边框、硬影 `3px 3px 0 0 <模块色>`、微倾 `-0.8deg`
- **hover**：底 `color-mix(--app-highlight 28%, transparent)`、微倾 `-0.4deg`
- **未激活文字**：`--ink`（⚠️ **不是** `--app-nav-text`；那个令牌实际由设备管理卡片、AI 工具箱消费）
- 图标块 22×22（子项 18×18）、2px 墨框、底 = 模块色
- **已知缺口**：`prefers-reduced-motion` 只关了 transition、未置 `transform: none` → 减动效下微倾仍生效（见 [../known-gaps.md](../known-gaps.md)）

**侧栏图标用 Lucide**（`data-lucide` + `window.lucide.createIcons()`），映射真相源 `frontend/src/shared/components/sidebarNavConfig.ts`：

```javascript
const NAV_ICONS = {
  dashboard:       'layout-dashboard',
  device_pool:     'smartphone',
  element_locator: 'crosshair',
  case_manager:    'layers',
  test_runner:     'play-circle',
  report:          'file-bar-chart',
  ai_assistant:    'bot',
  workflow:        'git-branch',
  digital_human:   'user-round',
}
```

> 模块内业务组件用 `shared/icons/index.ts` 的 `makeIcon` 自定义 SVG，与侧栏 Lucide 是**两套体系**。改图标前先确认目标组件用哪套。

## 4. `.doc-section` 页面级分区

带标题的一大段内容用 `.doc-section`（标题 + 可选提示 + 分隔虚线），**不要**用 `AppCard` 当分区外壳。分区内部的卡片网格见 [cards.md](cards.md)。页面层的完整骨架与滚动规则见 [../page-layout.md](../page-layout.md)。

## 5. AppTabs / FilterTabs

- **AppTabs**（`.ac-tabs`，仅 `.wb-shell` 内）：header 下边距 `--app-space-md`；隐藏 `nav-wrap::after` 与激活下划线；item 圆角 `--app-radius-sm`、内边距 `5px 14px`、字 `--app-size-xs` / 700；**激活** 底 `--c-dashboard` + 墨框，未激活字 `--app-text-secondary`
- **FilterTabs**（原生 button）：未激活 底白 + `1px solid --app-border-light`（近白，属占位）+ 圆角 `--app-radius-pill` + 无阴影；**激活** 底 `--app-bg-subtle` + 墨框；hover 只变字色；`count` 角标 `--app-font-mono` / 18px / 圆角 pill
- **已登记例外**：device-pool 在 `.device-workbench` 内把 FilterTabs 改成 `2px` 实框 + 硬影 + 未选天蓝 / 选中柠黄
- **已知缺口**：FilterTabs 无 `role=tab` / `aria-pressed`，无 reduced-motion 降级（见 [../known-gaps.md](../known-gaps.md)）
