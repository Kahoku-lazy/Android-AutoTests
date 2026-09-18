## Context

动机见 `proposal.md` - Why。

现状：
- L1 侧栏在 `AppSidebar.vue` + `AppSidebar.style.css`
- 视觉：`--paper` 底 + `border-right: 3px solid var(--ink)` + active 左侧模块色书签条
- 图标：Lucide（`data-lucide`）
- 文案：`sidebarNavConfig.ts` 的中文 label

原型 `temps/hand-drawn-doodle-sidebar.html` 侧栏口径：
- 底 `#fffdf8`，右边 `2.5px dashed ink`
- brand：黄方块 mark + 青偏移阴影 + 虚线底边
- nav-item：hover 浅黄微倾；active 黄底 + dashed 边 + `box-shadow: 3px 3px 0 teal`（可按页换阴影色）
- nav-ico：22×22 白底墨边方盒

约束：文案与 SVG 保留；颜色走令牌；不改路由/折叠/账号逻辑。

## Goals / Non-Goals

**Goals:**
- 侧栏 chrome / brand / nav / footer 视觉对齐原型
- Lucide 外包方盒；active 阴影用模块色
- 折叠与展开都可读

**Non-Goals:**
- 不改主区 PaperDoodles、不改顶栏结构
- 不把导航图标改成原型字母方块
- 不改 `NAV_CATEGORIES` 的 path/label/icon 数据（除非仅加展示 class）
- 不重做账号菜单交互

## Decisions

### 1. 主要改 `AppSidebar.style.css`，模板只做最小结构补丁

- **选择**：样式为主；`AppSidebar.vue` 仅在品牌区增加 `.brand-mark` 容器（可放「AI」二字或短标），导航项给图标外包 `.nav-ico` 类
- **理由**：行为与文案不动，降低回归面
- **备选**：整文件重写组件 — 风险大，拒绝

### 2. 颜色映射（模板 → 主题令牌）

| 模板 | 令牌 |
|------|------|
| `--ink` `#2c2c2c` | `var(--ink)` |
| `--paper` / sidebar `#fffdf8` | `var(--paper)` 或略暖 `#fffdf8` 若与 `--paper` 极近则直接 `--paper` |
| `--yellow` `#ffd93d` | `var(--app-highlight)` / `var(--c-dashboard)` |
| `--teal` `#4ecdc4` | `var(--c-case)`（青绿）作默认偏移阴影 |
| 模块强调 | 现有 `--mod-color` / `MOD_COLORS` |

虚线：`2.5px dashed var(--ink)`（可用本地 CSS 变量 `--sidebar-dash`）。

### 3. active 阴影用模块色，而不是清一色 teal

- **选择**：`box-shadow: 3px 3px 0 0 var(--mod-color, var(--c-case))`
- **理由**：保留平台「每模块一色」信息，同时符合原型偏移色块语言
- **备选**：全用 teal — 更像静态展板，丢模块识别

### 4. 图标：保留 Lucide，加方盒

- **选择**：`.nav-lucide-icon` 外包裹或自身做成 22×22 方盒（白底、2px ink 边、小圆角 2px）
- **理由**：用户要求 SVG 样式保留 + 颜色按主题
- **备选**：换成字母 — 明确禁止

### 5. 去掉粗实线与旧书签条

- **选择**：右侧实线 → 虚线；active 左侧 4px 色条可移除或弱化，避免与黄底板双重强调打架
- **理由**：对齐原型单一强调语言

### 6. 品牌字重

- **选择**：保留现有品牌字体令牌；布局改为 mark + 标题行，避免为追原型强行换 Albert Sans CDN
- **理由**：主题令牌优先，不新引入外链字体

## 模块防火墙自检

- 跨 App / 写库 / 前端直连 DB：不涉及
- 仅 L1 shared 组件样式与少量 DOM 结构

## Risks / Trade-offs

- [飞扬体 + 黄底板可能拥挤] → 控制 brand 字号与 padding；折叠态只留 mark
- [虚线在高 DPI 发虚] → 2.5px dashed；验收时看 Win/Chrome
- [子菜单项也套黄底可能过噪] → 子项 active 可用更薄样式（左边虚线或浅黄），父级/叶子主项用满配黄底
- [与旧截图/E2E 类名] → 保留 `data-testid` 与主要 BEM 根类 `.sidebar`

## Migration Plan

1. 补品牌 mark DOM + 图标方盒 class
2. 重写侧栏 CSS 关键规则（边框/底/hover/active/footer）
3. 目视：展开、折叠、多模块 active、账号菜单
4. 回滚：还原 vue/css 即可
