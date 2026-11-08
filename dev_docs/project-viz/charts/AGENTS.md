# charts AGENTS.md — 统一图表底层

> 层级：根 [`AGENTS.md`](../../../AGENTS.md) → [`project-viz/AGENTS.md`](../AGENTS.md) → **本文件**。
> 本目录只做"怎么画"，不做"画什么"；数据来自 `../data/`，视觉令牌来自 `frontend/src/shared/styles/tokens.css`。

## 为什么有这个目录

图表最容易长成"每个图各写一套"：各自 `echarts.init`、各自写死颜色、各自忘了 `dispose`、各自不处理 resize。
所以这里把**共性抽成一层**，图与图之间的差异只剩 `option`：

```
charts/chart-framework.js    生命周期 + 主题 + 组件（唯一允许碰 echarts.init 的地方）
        ▲
        │ 被 <viz-chart> 使用
charts/board-options.js      纯函数：数据 → ECharts option（看板的条形图 / 环形图）
        ▲
        │ 被 app.js 的 computed 调用
index.html                   声明式挂载：<viz-chart :option="…" height="…" />
```

## 做图表需要哪些方法（契约表）

**这一节就是"Agent 要记的东西"**：新增图表只允许用下列方法，不允许绕开。

| 能力 | 入口 | 签名 | 谁调用 / 说明 |
| --- | --- | --- | --- |
| 读主题令牌 | `VizCharts.tokens()` | `() => Theme` | app 启动时取一次。把 CSS 令牌翻成 ECharts 能吃的具体色值（canvas 读不到 `var()`），含 `ink/paper/card/subtle/secondary/stat/font/fontSize/reduceMotion/colors{frontend,backend,engine}` |
| 建实例 | `VizCharts.create(el, option)` | `(Element, Option) => Handle` | 内部 `echarts.init` + `ResizeObserver`；**唯一**允许初始化实例的入口 |
| 更新 | `handle.update(option)` | `(Option) => void` | 增量替换（`setOption(next, true)`）；组件在 option 变化时自动调 |
| 重排 | `handle.resize()` | `() => void` | 容器尺寸变化；一般不用手调（ResizeObserver 已挂） |
| 销毁 | `handle.dispose()` | `() => void` | 断开 observer + `chart.dispose()`；组件 `beforeUnmount` 自动调 |
| 注册组件 | `VizCharts.register(app)` | `(App) => void` | 在 `app.mount()` 之前调用；Vue 3 没有 `Vue.component`，必须传 app 实例 |
| 声明式挂载 | `<viz-chart>` | `option`（必填）、`height`（默认 `320px`）、`label`（无障碍名） | 页面里只写这一行；不许在页面里直接 `echarts.init` |
| 造配置 | `BoardOptions.totalsBar(board, theme, active)` / `bar(board, metricKey, theme, active, order)` / `donut(board, theme, active)` / `agentsBar(agents, theme)` / `agentsGraph(agents, theme)` / `agentsHistory(history, theme)` / `moduleBar(rows, theme, colorKey)` / `depGraph(nodes, edges, theme)` / `historyLine(history, catKey, theme)` | 纯函数，无副作用 | 只算数据、不碰 DOM；`moduleBar` 是单层总览条形（前端模块 / 后端 App），`depGraph` 是通用依赖图（agents 目录 / 前端模块 / 后端 App 共用，需要完整构建的 `graph`），`historyLine` 按分层键（frontend/backend/engine/agents）取历史 |
| 统一行序 | `BoardOptions.moduleOrder(board, active)` | `(board, active) => string[]` | 代码行降序 → 方法数降序 → 名字；**五张明细图必须共用一份**，否则同一模块在五图里位置不同，无法横向对照 |
| 范围合计 | `BoardOptions.scopeTotals(board, active)` / `scopeLabel(board, active)` | 纯函数 | 全仓或单分类的合计与标题文案，图表和标题共用，避免两处各算一遍 |
| 指标枚举 | `BoardOptions.metrics` / `totalsMetrics` | `[{key,label}]` | 明细图 5 个指标、总量图 6 个（多一个"模块"） |
| 数字格式 | `BoardOptions.fmt(value)` | `(number) => string` | 千分位；坐标轴标签 / tooltip / 表格共用 |

## 新增一张图表（照这个顺序，别跳）

> 现有配置：`totalsBar` 1 张、`donut` 1 张、`bar` **5 张**（功能/文件/类/方法/代码行，一指标一张，没有指标开关）。
> 五张图由 `app.js` 的 `metricCharts` 统一生成（同一 `active`、同一高度），所以筛选只改一个状态即可全量同步。

1. **定口径**：这个图回答什么问题、数据从哪来（先回 [`../AGENTS.md`](../AGENTS.md) 第 2 步）。
2. **写 option 构造器**：在 `board-options.js` 加 `function xxx(board, theme)`，**纯函数**，返回 option；颜色只从 `theme.colors` / `theme.*` 取。
3. **挂到页面**：`index.html`（看板）或 `agents.html`（智能体页）加 `<viz-chart :option="xxxOption" height="…" label="…" />`，对应 `app.js` / `agents.js` 加 `computed`。
4. **无数据保护**：数据为空时**不要**渲染空图（会看起来像"全是 0"）；用 `v-if` / 空态件挡掉。
5. **token 一致性**：`theme` 必须来自 `VizCharts.tokens()`；颜色、字号、字体不许写死字面量。
6. **自检**：`node --check` 三个 js + Playwright 打开（零 console）+ 缩放窗口看是否随容器重排 + 切分类筛选看是否只更新不新增实例（实例数应恒等于图表数）。

## 红线（违反即返工）

1. **禁止**在 `index.html` / `app.js` / 业务代码里直接 `echarts.init` 或 `new echarts.*`——只有 `chart-framework.js` 可以。
2. **禁止** CDN / 远程字体：ECharts 必须用 `../vendor/echarts.min.js`（**完整构建**，因为依赖图 `graph` 只有完整包有；与 `frontend/package.json` 的 `echarts` 同版本升级）。
3. **禁止**写死颜色 / 字号：一律经由 `VizCharts.tokens()`；ECharts 是 canvas，读不到 CSS 变量，这是唯一例外，但值必须来自令牌。
4. **禁止**忘记销毁：任何自建实例都要 `dispose()` 并断开 `ResizeObserver`，否则切视图会泄漏。
5. **禁止**零高度容器：`<viz-chart>` 必须给 `height`（canvas 在 0×0 容器里初始化会画不出来）。
6. **禁止**假数据：没有真实数据就不画图、不填 0；空即空。

## 已踩过的坑

- **Vue 3 没有 `Vue.component`**：全局组件必须 `app.component(...)`；`VizCharts.register(Vue)` 会抛 `Vue.component is not a function`，页面直接白屏（骨架能看见、插值没编译，症状很有迷惑性）。
- **切换指标不要重建实例**：`<viz-chart>` 监听 `option` 深度变化后走 `setOption(next, true)`，重复 `init` 会叠 canvas 且泄漏。
- **`ResizeObserver` 是必需项**：侧栏固定宽 + 主区 `flex`，窗口一缩图表不会自动变宽；只靠 `window.onresize` 漏掉容器内变化。
- **ECharts 扇形/条形描边**：想保持"粗线涂鸦"观感，用 `itemStyle.borderColor = theme.ink` + `borderWidth: 1~2`，不要用阴影（阴影模糊半径必须为 0 的口径）。
- **长 Y 轴标签**：模块名超过 16 字要截断（`BoardOptions.shortName` 已处理），完整名放 tooltip，否则标签会压到图上。
- **窄卡片里别用饼图外置标签**：`代码行占比` 卡只占 1/3 宽，`label` 放外面会被裁成 "前端 49…"；改成内置百分比（压边）也不行。最终把百分比交给底部 `legend.formatter`，扇区只负责面积。
- **6 个指标不能共用线性轴**：模块 29 与代码行 51,086 同轴时前 5 条会被压成一条线。用 `xAxis.type = "log"`（`min: 1`，避免 0 取不到对数），并在卡片上写明"对数刻度"。
- **筛选入口只留一个**：分类筛选是**全局**状态，只在**页头**（`.wb-header`，吸顶）出现；曾经在「分层明细」里又放了一排同功能的图例按钮，两处入口 + 滚动时看不见，交互很差，已删。分类颜色改成页头按钮上的小色块（`.seg__dot`），图例与筛选合并。表格 `tbody` 也按 `visibleCategories` 渲染，`tfoot` 仅在"全部"时出现（单分类时小计即全部）。
- **别在内容区复刻全局控件**：凡"全局筛选/全局开关"，只在页头放一次；内容区只放**只读**说明（如"条形颜色对应分类：前端/后端/引擎"），否则用户要滚回顶部才能改，或者以为两处状态不同。
- **多图必须共用行序**：五张明细图各自按自己的指标降序时，同一个模块在五张图里位置不同，跨图对照要靠肉眼找名字。改成 `moduleOrder()` 统一排序后，同一行就是同一模块——新增多指标图时记得把 `order` 传进去，别在 `bar()` 里再排一次。
- **排序变了但高度没变**：高度按行数算（`rows*22+64`），与排序无关；若以后加"只显示 Top N"，记得高度也要跟着可见行数走，否则底部留白。
