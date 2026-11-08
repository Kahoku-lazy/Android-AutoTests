# 项目可视化

> 目的：把**当前这个仓库**可视化出来——不用翻代码就能看懂"有哪些模块、各占多少、谁依赖谁、一次任务怎么跑"。
> 现状：第一个视图已落地——**项目看板**（前端 / 后端 / 引擎三层的模块量与功能面）；数据是**静态快照**，代码变了要重跑生成器。
> 目录约定与红线见 [AGENTS.md](AGENTS.md)（给改这个目录的人 / AI 看）。

## 打开

五个独立页面，双击对应文件即可（无需 Node、无需联网、无需构建；Vue / ECharts 已本地化在 `vendor/`）：

- `index.html` —— **总览**（结论页：领域打通率 / 引擎能力 / 健康分 / 最近变化 + 领域矩阵；**不画图表**）
- [board.html](board.html) —— **明细看板**（三层模块量 + 五张明细图，带全局分类筛选）
- [frontend.html](frontend.html) —— **前端功能模块**（`frontend/src`，五层）
- [backend.html](backend.html) —— **后端功能模块**（`backend/apps`，五层）
- [agents.html](agents.html) —— **智能体功能模块**（引擎 `engines/agents`，五层）

五个页面**不共享视图层**（各有一份侧栏与页头、各自的 js），只共享 `styles.css`、数据快照与 `charts/`。

页面之间用侧栏链接互跳。需要固定端口时：

```bash
python -m http.server 8811 --directory dev_docs/project-viz
# 看板 http://127.0.0.1:8811/index.html
# 智能体 http://127.0.0.1:8811/agents.html
```

## 页面结构

### 页面一：项目看板（`index.html`）

| 分区 | 内容 |
| --- | --- |
| 页头筛选 | `全部 / 前端 / 后端 / 引擎`：**唯一入口、吸顶常驻**（滚到哪都能点），按钮上的小色块就是分类色，兼作图例；一个状态贯通总量图、占比高亮、五张明细图与表格 |
| 1. 总量 | 两张图并列：**左** = 当前范围总量（6 项指标，对数横轴，标签给真实值）；**右** = 代码行占比（按分类，筛选时只高亮不隐藏） |
| 1. 分层明细 | **五张图，一指标一张**：功能 → 文件 → 类 → 方法 → 代码行（宽屏两列，第五张通栏）。每张图是"按模块"的横向条形、按分类上色；表格收在「明细数据」折叠区 |
| 2. 口径与数据源 | 每个指标的统计口径、生成命令、生成时间与 commit |
| 3. 下一步（待定） | 还没做的视图，明确标"待定" |

### 页面二 / 三：前端、后端功能模块（`frontend.html` / `backend.html`，结构同下）

与「智能体功能模块」同一套五层结构，替换数据来源即可：

| 层 | 前端 | 后端 |
| --- | --- | --- |
| 1 数据总览 | 11 个模块（含共享层）· 功能=路由条目 | 13 个 App（含基础设施）· 功能=API 端点 |
| 2 依赖关系 | 模块级 import 图（`@/` 别名 + 相对路径，TypeScript 语法树） | App 级 import 图（AST；能看到调用面，**看不出是否走了 api**） |
| 3 流程 / 时序 | 进入应用 → 守卫 → 路由 → 页面 → API → 展示（`data/flow-frontend.js`） | 网关 → urls → View → Serializer → api → 落库响应（`data/flow-backend.js`） |
| 4 功能模块说明 | 每个模块折叠展开 **路由清单**（path/name/标题） | 每个 App 折叠展开 **文件构成**（文件名/类/方法/行数） |
| 5 页面构成（仅前端） | 15 个页面的**结构示意**（页头/KPI/筛选/表格/表单/抽屉 的固定块序）+ 共享与本地子组件 + 交互件计数 + 模块调用的 71 个接口 | — |
| 6 历史趋势 | 前端代码行折线（`history.json` 的 `frontend` 段） | 后端代码行折线（`backend` 段） |

### 页面四：智能体功能模块（`agents.html`，独立页面，五层）

页内用顶部「分层导航」跳到五层，每层各回答一个问题：

| 层 | 回答什么 | 数据来源 |
| --- | --- | --- |
| 1. 数据总览 | 有多大：模块 / 功能条目 / 类 / 方法 / 代码行 / 测试；按目录的代码行条形图 + **目录 Tab 切换的模块表**（一次一个目录，省版面） | `board.json` 的 `agents` 段（AST + docstring） |
| 2. 依赖关系 | 谁依赖谁：目录级有向图（边=跨目录 import 次数），加"同目录内部依赖"与"跨目录模块对 Top 20"两张清单 | 同上 `agents.imports`（**AST 静态解析，不等于运行期调用链**） |
| 3. 流程 / 时序 | 一次任务从下发到展示的六步，每步写清角色、动作、产物与**来源文件** | `data/flow.js`（**人工维护**，附 caveat） |
| 4. 功能模块说明 | 每个模块的一句话职责、类型、调试入口（全部取自模块 docstring） | `board.json` 的 `agents.groups` |
| 5. 历史趋势 | 模块量随时间变化；每次生成追加一个快照，≥2 个才画折线，否则明确说"还需要至少 2 个快照" | `data/history.json`（生成器追加，保留最近 60 次） |

这页**不共享**看板的视图层：自己有页头（无分类筛选）、自己的侧栏与 `agents.js`；**共享** `styles.css`、数据快照与 `charts/` 图表底层。

图表不各写一套：统一走 [`charts/chart-framework.js`](charts/chart-framework.js)（实例生命周期 / 容器 resize / 令牌主题 / `<viz-chart>` 组件），契约见 [`charts/AGENTS.md`](charts/AGENTS.md)。

## 目录

| 路径 | 作用 |
| --- | --- |
| `index.html` | 页面一：项目看板骨架与 Vue 模板 |
| `agents.html` | 页面二：智能体功能模块（独立页面） |
| `styles.css` | 两页共用：令牌子集 + 骨架样式 + 组件配方（图表卡 / 表纸 / 空态） |
| `app.js` | 页面一的 Vue 应用：读 `window.__BOARD__`、渲染看板 |
| `agents.js` | 智能体页应用：读 `__BOARD__.agents` / `__HISTORY__` / `__FLOW__`，渲染五层 |
| `board.html` | 明细看板（原 `index.html` 的内容搬过来；`app.js` 仍由它加载） |
| `overview.js` | 总览页应用：只读 `__BOARD__.overview`，不画图表 |
| `tools/domains.json` | **业务域对照表（人工维护，10 行）**：域 → 前端模块 / 后端 App / 引擎目录 / 支撑档位 |
| `frontend.html` · `frontend.js` | 前端页：模块行 + 路由清单 + 模块级依赖图 + 历史折线 |
| `backend.html` · `backend.js` | 后端页：App 行 + 文件构成 + App 级依赖图 + 历史折线 |
| `data/history.json` · `data/history.js` | 历史快照（生成器每次追加，数值没变不追加；保留最近 60 次） |
| `data/flow.js` · `flow-frontend.js` · `flow-backend.js` | 三个页面的流程 / 时序（**人工维护**，每步带来源文件），不是采集结果 |
| `data/board.json` | 快照本体（机器可读，供别的脚本消费） |
| `data/board.js` | 同一份数据以 `window.__BOARD__ = …` 形式给页面用（`file://` 下 `fetch` 会被 CORS 拦掉） |
| `tools/gen_board_data.py` | 生成器：扫仓库 → 写上面两个数据文件 |
| `tools/count_frontend.mjs` | 前端计数：用本地 TypeScript 编译器做语法树统计 |
| `charts/chart-framework.js` | **统一图表底层**：`VizCharts.tokens/create/register` + `<viz-chart>` |
| `charts/board-options.js` | 纯函数：看板数据 → ECharts option（条形 / 环形） |
| `charts/AGENTS.md` | 图表契约：需要哪些方法、怎么加一张图、红线与已踩坑 |
| `vendor/vue.global.prod.js` | Vue 3.5.44 全局构建（从 `frontend/node_modules/vue/dist/` 复制，离线可开） |
| `vendor/echarts.min.js` | ECharts 5.6.0 **完整构建**（从 `frontend/node_modules/echarts/dist/` 复制，离线可开；依赖图的 `graph` 只有完整包有） |

## 数据怎么来

```bash
python dev_docs/project-viz/tools/gen_board_data.py           # 重新生成快照
python dev_docs/project-viz/tools/gen_board_data.py --check   # 只比对现有快照是否过期（过期退出码 1）
```

| 指标 | 口径 |
| --- | --- |
| **功能** | 前端 = `routes.ts` 注册的路由条目数；后端 = DRF API 端点数（`utils/gen_arch_stats.py`）；引擎 = 模块 docstring「简介说明」声明的能力条目数。**三层口径不同，只做各自量级对照，不可横向相加比较。** |
| 文件 | 代码文件数（`.py` / `.vue` / `.ts` / `.js`）；排除 `__pycache__`、`migrations`、`vendor`、`skill-creator` |
| 类 | `class` 定义数（Python `ClassDef` / TypeScript `ClassDeclaration`） |
| 方法 | 命名函数 / 方法定义数；不含 `lambda` 与匿名回调 |
| 代码行 | 非空物理行（前端含 `template` / `style`） |

范围：后端含一行「基础设施（gateway/config/models/shared）」；前端含一行「共享层（shared/views/router）」；引擎按一级子包汇总（不含 `engines/__init__.py`）。

## 已定 / 未定

**已定**

1. 三层分类口径：前端 = `frontend/src/modules/*`，后端 = `backend/apps/*`，引擎 = `engines/<子包>`。
2. 指标口径（见上表）与数据来源（静态快照 + 生成器，不调后端接口）。
3. 版式：沿用 doodle-craft 默认（纸面 + 粗线 + 硬影 + 微倾 + 表纸）。
4. **图表底层统一**：ECharts 5.6.0 本地化 + `charts/chart-framework.js` 一套生命周期/主题/组件；新图表只写 option，不重复造壳。
5. **总量也图表化 + 全局分类筛选**：`全部/前端/后端/引擎` 一个状态贯通页头、总量图、占比高亮、五张明细图与表格；总量图用**对数横轴**（6 项指标量级差大，线性轴会把小值压平）。
6. **明细拆成五图**：功能 / 文件 / 类 / 方法 / 代码行各一张，不再用指标开关；筛选一次同步刷新五张（连同轴高度一起变）。
7. **五图统一排序**：行顺序固定为"代码行降序 → 方法数降序 → 名字"，所以**同一个模块在五张图里永远同一行**，可横向对照；不再按各自指标排序。
8. **引擎下钻视图**：`engines/agents` 按目录建模（模块数 / 功能条目 / 类 / 方法 / 代码行 / 测试），数据与看板同一份快照（`board.json` 的 `agents` 键），同一命令生成。
9. **智能体功能模块是独立页面**（`agents.html` + `agents.js`）：不与看板共享视图层——自己的页头（无分类筛选）、自己的侧栏与脚本；只共享 `styles.css`、数据快照与 `charts/` 图表底层。侧栏两页各一份，改动时需同步（见 AGENTS 已知坑）。
10. **智能体页分五层**：数据总览 / 依赖关系 / 流程时序 / 功能模块说明 / 历史趋势；依赖图来自 AST import（静态），时序来自 `data/flow.js`（人工维护、带来源与 caveat），趋势来自生成器追加的 `history.json`（不足 2 个快照就显示空态）。

**未定（别擅自补）**

1. **依赖关系视图**：谁 import 谁（引擎 docstring 的「关联模块」与 AST import 交叉校验）。
2. **流程 / 时序视图**：一次任务从下发到报告经过哪些角色与中间件。
3. **按功能下钻**：点开一个模块看它的功能清单、入口与测试归属。
4. **历史趋势**：需要多次快照存档后再看（现在只有单点快照）。

## 约束（改这个目录前先看）

- **视觉**：遵循 `.agents/skills/doodle-craft`。颜色只用 `var(--…)`，字号 / 间距 / 圆角 / 阴影取刻度，阴影模糊半径恒 0，卡片按序号微倾、hover 回正，动 `transform` 的类必须有 `prefers-reduced-motion` 降级。
- **令牌真相源**：`frontend/src/shared/styles/tokens.css`。这里只抄了用到的子集；要加新令牌先改真相源，再同步本目录。
- **不污染平台**：本目录不参与 `frontend/` 的 Vite 构建与 lint 门禁，也不被后端引用。
- **占位不得冒充结论**：没数据就显示"还没有数据快照"，不显示 0 当真；没定的视图继续标"待定"。
