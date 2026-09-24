# Doodle Craft 页面层 — 布局骨架与滚动规则

> 来源：本文件（页面层规则以此为准）。**令牌值唯一真相源是 `frontend/src/shared/styles/tokens.css`**，检索表见 [tokens.md](tokens.md)。
> 与 `openspec/specs/frontend-l0…l5-*` 同口径；两者冲突时以代码 + 门禁为准。
> 相邻参考：组件层（页头 / 侧栏 / 卡片 / 表格…）见 [components/](components/)；场景落地见 [vue-project.md](vue-project.md) 与 [standalone-html.md](standalone-html.md)。

## 4.0 L0–L5 分层与归属（先判层，再动手）

区域是 UI 的横切分层，**模块只拥有自己页面的 L2–L5，不拥有 L1**。

| 层 | 范围 | 归属 | 关键约束 |
|:--:|------|------|----------|
| L0 | 视口纸面 + 主区涂鸦层 | 外壳 | 暖白实色；涂鸦只挂主内容区、不拦指针、不进侧栏（见 4.2）|
| L1 | 侧栏（默认 260px，可拖拽 180–360，折叠 64px）+ 主区壳 | 外壳（模块**不许改**）| 主区是唯一路由出口；`keep-alive :max="5"` 与 `:key="route.path"` 不得改动 |
| L2 | 页头 + 页面根 | 模块 | 页头只有唯一共享件（高 `--app-topbar-h`、`z-index: --z-header`、与侧栏品牌区底边对齐）；页面根 `doc-page`（固定视口页加 `doc-page--fixed`）且**必带主题作用域 `wb-shell`** |
| L3 | 正文容器 + 分区 / 数据块 | 模块 | 唯一纵向滚动在 `.doc-body`；页面级分区用 `.doc-section`，可复用数据块用 `AppCard` |
| L4 | 表格 / 卡片网格 / 表单 | 模块 + shared 零件 | 表格只用共享 `AppTable`；分页只用 `usePagination`；卡片零件只用 shared |
| L5 | 弹窗 / 抽屉 / 确认框 | 模块 + Element Plus | 一律走 EP 覆盖层；禁自建遮罩、禁浏览器原生弹窗 |

**登记例外**（不算违规，但不得扩散）：

| 例外 | 内容 |
|------|------|
| 画布类页面 | `/workflow/prototypes/:prototypeId` 主体用 `.wb-body`（自由布局画布），是全仓唯一非 `.doc-body` 的页面主体 |
| 工作区分栏页 | 以分栏而非分区组织内容的页面（如 `/inspector`：`.inspector-section` + `.workspace`）不要求引入 `.doc-section` |
| 登录页 | `/login` 无侧栏、独立视觉壳（Meeting doodle），不走工作台骨架 |

## 4.1 标准页面骨架

```
┌──────────────────────────────────────────────┐
│ AppSidebar (默认 260px) │ WorkbenchHeader        │  z-index: --z-header (10)
├────────────────────┼──────────────────────────┤
│                    │ KPI 统计条 / 操作工具栏    │  操作区
│                    ├──────────────────────────┤
│      侧边栏        │ 筛选标签 + 视图切换        │  筛选区
│                    ├──────────────────────────┤
│                    │ 主内容区                   │  唯一纵向滚动
│                    │  · 卡片网格 / 表格 / 详情  │  flex: 1 1 0
│                    │                          │  min-height: 0
│                    │                          │  overflow-y: auto
└────────────────────┴──────────────────────────┘
```

自上而下：侧边栏+顶栏 → 操作区 → 筛选区 → 主内容区（唯一纵向滚动）→ 页脚（**可选、页面自备**，外壳不提供全局页脚）。

## 4.2 页面背景（暖白纸面 + 主区涂鸦）

```css
/* L0 / 壳层：纯暖白纸面，禁止点阵与横线本 */
background-color: var(--paper); /* #fffef5 */

/* 主区稀疏涂鸦：shared/components/PaperDoodles.vue
   position:absolute; inset:0; pointer-events:none; 挂在 .main-content 内 */
```

全站统一暖白纸面 + 主内容区稀疏 SVG 涂鸦（对齐 `temps/hand-drawn-doodle-sidebar.html`）。
**禁止**点阵纸纹、横线本作为全站/工作台背景；**禁止**在 `.doc-page--fixed .doc-body` 再叠第二套纸纹。
侧栏保持干净，不挂涂鸦层。

## 4.3 卡片网格微旋转

页面侧的要求只有一条：**网格必须有微倾，禁止全部 0deg 排排坐**；机制与取值（`sketchTiltAt(i)` / `SKETCH_TILTS` / `nth-child` 三值轮转的 CSS 片段）见 [components/decorative.md](components/decorative.md) §2。

微倾请走那两种机制之一，**不要就地写行内 `transform`**——它会压掉 hover 回正。

## 4.4 滚动规则

| 区域 | 滚动 | 规则 |
|------|:--:|------|
| 页面主内容区 | 纵向 | `flex: 1 1 0; min-height: 0; overflow-y: auto` |
| 表格 | 横向 | `overflow-x: auto` + 固定表头 |
| 卡片 | 禁止 | 卡片本身不设滚动，溢出裁剪或外部容器滚动 |
| 弹窗内容 | 禁止 | 弹窗不设内部滚动 |

**关键**：禁止任何中间层出现 `overflow: hidden`，会导致内容被裁剪。翻车记录：`info-card` 残留 `overflow:hidden` + `el-tabs__content` 的 `overflow:hidden` 三层裁剪。

## 4.5 内容区 Flex 子项规则

```css
.content-area {
  flex: 1 1 0;        /* 必须，占满剩余高度 */
  min-height: 0;      /* 必须，覆盖 min-height:auto */
  overflow-y: auto;   /* 必须，唯一纵向滚动容器 */
}
```

三个属性缺一不可，缺了内容溢出时页面无法滚动。

## 4.6 内容区宽度规则

**禁止在全局样式对内容区设 `max-width` 并居中**，各模块自己决定。

| 场景 | 是否 max-width | 理由 |
|------|:--:|------|
| 仪表盘、设备管理（卡片网格/表格/图表） | ❌ | 内容密度高、多列布局 |
| 元素定位（左目录树 + 右元素表并排） | ❌ | 左右分栏，限宽会压右栏表格 |
| 长文本阅读、Markdown 渲染 | ✅ 700–900px | 阅读舒适度 |
| 表单填写页 | ⚠️ 可选 800px | 光标移动距离 |

翻车记录：全局 `.doc-body` 设 `max-width: 1600px; margin: 0 auto`，导致大屏（2560px+）两侧各 ~480px 空白，已移除。

## 4.7 标准页面模板（3 变体）

| 你的页面是…… | 用哪个变体 | 示例模块 |
|------------|:--:|------|
| 卡片网格 + KPI 统计 | 变体 A | dashboard、device-pool |
| 表格列表 + 筛选栏 | 变体 B | report-generator、test-runner |
| 左侧树/面板 + 右侧内容 | 变体 C | element-locator、case-manager |

> 每个变体复制后改 KPI 字段 / 筛选标签 / 卡片字段 → 完成。表格页把 `.cards` 换成 `el-table`。

### 4.7.1 变体 C 的树栏规格（工作台类页面）

由变更 `relayout-locator-workspace`（元素定位项目工作台）确立，姊妹模块可照抄：

| 维度 | 规格 |
|------|------|
| 版式 | 左栏固定档位宽度目录树 + 分隔手柄 + 右栏选中项内容；左栏宽度 MUST 取 T0 档位 `--layout-pane-left`（280px，模块令牌 `--<mod>-tree-pane-w: var(--layout-pane-left)` 转发，**不得**在模块里写宽度字面量），右栏 `minmax(0, 1fr)` |
| 左栏可拖动 | 两栏之间 MUST 有 `SplitHandle`（共享件）：鼠标左右拖动改宽度、常态暖灰分隔线 + hover/拖动转墨色、`col-resize` 光标与拖动期正文不可选；宽度夹在 **220px ~ min(560px, 容器宽 − 360px)**；← / → 步进 16px（Shift 48px）、Home / End 到两端、双击复位到 T0 档位；宽度按模块记忆（`app-split-<mod>-tree-w`）；窄屏未并置时 MUST NOT 渲染手柄。**不得**给窗格再画第二条分隔线（线由手柄独占） |
| 右栏职责 | **只读预览，不承担编辑**：右栏 MUST NOT 出现行内编辑、勾选、新增 / 删除、开关等写控件，只给一个「进入页面编辑」入口（唯一，固定标题行）。编辑一律进叶子整页 |
| 姊妹模块 | 元素定位工作台与用例管理工作台共用同一分栏壳：左树 + 右只读预览。元素定位预览给三列（缩略图 / 元素名称 / 序号），用例预览给五列（用例 ID / 测试类型 / 业务类型 / 标题 / 时间）；两处都分页可达全部（每页 10 行 + 上一页 / 下一页）|
| 两模块逐项同源 | 树的**行皮肤与工具栏**必须逐项一致：行 `border: 2px solid transparent`（默认无可见描边）+ 悬停模块色 10% 底色 + 选中 `border-color: var(--ink)` + `--app-shadow-sm` + 16% 底色；行圆角 `--app-radius-md`、内边距 `var(--app-space-xs) var(--app-space-sm)`；缩进 ≥18px + 子层 `2px dotted var(--color-orange-76)` 引导线；文件行「进入 ›」紧贴名称、目录行尾随子项数（0 显示「空」）；工具栏按钮 hover 左上 1px、disabled 半透明、危险态红底浅色字；工具栏**不得**常驻静态位置面包屑。差异只允许：模块色、右栏列集、业务动作文案 |
| 树行的职责边界 | 树行**只表达结构与名称**：图标 + 名称 + 紧贴名称的「进入 ›」；目录行尾随子项数（0 显示「空」）。**数据列信息（更新时间等）MUST NOT 出现在树行内**——数据列一律在右栏预览与叶子整页承载。理由：左栏是固定窄宽度，行内每多一个信息块就压缩名称；实测把时间塞进行内会让名称只剩约 4 个字 |
| 栏间分隔 | `2px solid var(--app-border-light)`；右栏不重复画框 |
| 树行默认态 | **不绘制可见描边**：用 `2px solid transparent` 占位（避免 hover/选中时行高跳动）；悬停给底色，选中行给 2px 墨框 + `--app-shadow-sm` |
| 层级表达 | 缩进 ≥ 18px（el-tree `indent`）+ 子层容器左边界 `2px dotted var(--color-orange-76)` 引导线；**不得**只靠 < 18px 缩进 |
| 目录行 | 尾随直接子项数；子项为 0 时显示「空」，**不显示 0** |
| 页面行 | 进入指示紧贴名称（名称 `flex: 0 1 auto`、尾部 `flex: 1 1 auto` 吸收剩余空间），**不得**把指示推到行尾远端 |
| 拖拽落点区 | **只在拖拽进行中或批量选择模式下渲染**，平时不占行；落点判定与端点不变 |
| 点选行为 | 宽屏（≥1280px）点条目写本地选中态、**不跳路由**；窄屏点条目跳该叶子路由（沿用既有两页流程） |
| 详情皮肤 | 右栏与叶子整页共用同一份硬边按键皮肤文件（`elementDetailSkin.css`，作用域类 `.element-detail-pane`），**不得**两处各写一套 |
| 右栏表格 | **只读预览，只给三列**（缩略图 / 元素名称 / 序号），并**分页可达全部**（每页 10 行 + 「第 X / Y 页 · 共 N 条」+ 上一页 / 下一页，边界禁用）；文本 / 主定位 / 交互标注 / 测试点四列**只在叶子整页**呈现。编辑（行内改 / 新增 / 删除 / 测试点开关）同样只在叶子整页，右栏 MUST NOT 出现写控件，只给一个「进入页面编辑」入口 |
| 待办 | 工作台的宽屏阈值目前写 `1280px`，T0 登记的档位是 `lg = 1200px`（tokens.css 注明该迁移需视觉确认）；两处工作台统一迁移另立一单 |


## 4.8 数据加载骨架与三态

所有 fetch 页面用同一骨架（script + template），只改标注「← 改这里」的部分：导入 api、数据变量名、API 调用、响应字段、错误文案、模板内容。

**三态必须用共享件，不得各写一套**：

| 状态 | 共享件 | 禁区 |
|------|--------|------|
| 加载中 | `patterns/SkeletonCard.vue` | 全屏 spinner、模块私有 shimmer/`__loading` 容器、裸 `el-skeleton` |
| 取数失败 | `patterns/ErrorState.vue`（带重试） | 白屏、`el-alert` 顶替错误态 |
| 取数成功但为空 | `patterns/EmptyState.vue` | 加载期间渲染空态（**假空态**）|

判定语：「数据为空」与「还没取完」必须由加载态区分。弹窗/抽屉/面板内的**原地**异步操作（保存、加载子内容）可用 `v-loading`；表格加载走 `AppTable` 的 `loading`。

> 完整代码模板可从 git 历史恢复。
