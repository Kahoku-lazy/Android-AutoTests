# project-viz AGENTS.md

> 层级：根 [`AGENTS.md`](../../AGENTS.md) → **本文件**。本文件只约束 `dev_docs/project-viz/`，不改平台代码；与上级冲突时以上级为准。

## 这个目录为什么存在

**一句话**：把**当前这个仓库**可视化出来——让人不用翻代码就能看懂"有哪些模块、谁依赖谁、一次任务怎么跑"。

几条创建时的判断，避免以后被误解：

1. **它是文档级产物，不是平台功能。** 放 `dev_docs/` 而不是 `frontend/`：不进 Vite 构建、不接后端接口、不参与 CI 门禁。**入口就是根目录的 [`index.html`](index.html)**——clone 下来双击它就能看，不需要装 Node、不需要起服务。其余 26 个页面（4 个分类页 + 22 模块页）收在 [`html/`](html/) 子目录，避免根目录平铺；JS / CSS / 数据 / 图表 / vendor 留在根。**两套相对路径**：入口页资源写同级（`styles.css`），`html/` 里的页面写 `../`。
2. **它是五个页面，每页三节。** ①「总览」（仓库一级目录）；②③④⑤「前端 / 后端 / 引擎 / 原型链路」——每页都是**三节**：模块关系图 / 依赖 + 代码量饼图 / 各模块单元代码量（带最近三次对比）。五页**不共享视图层**（各自一份侧栏与页头、各自的 js），只共享 `styles.css`、数据快照与 `charts/`。数据都是**静态快照**（`tools/gen_board_data.py` 生成）。
3. **它用 Vue，但不打包。** 选 Vue 是为了后续视图（关系图 / 时序 / 过滤交互）写起来比手写 DOM 省事；`vendor/vue.global.prod.js` 是本地化的 Vue 3 全局构建，保证断网可开。
4. **视觉沿用平台默认。** 用 [doodle-craft](../../.agents/skills/doodle-craft/SKILL.md) 的纸面 + 粗线 + 硬影 + 微倾，不另造一套风格——这页代表的是这个仓的既有视觉。

## 目录职责

| 路径 | 职责 | 谁改 |
| --- | --- | --- |
| [`index.html`](index.html) · [`overview.js`](overview.js) | **入口 / 总览（首页）**：仓库一级目录的三节看板（关系图 / 依赖 + 代码量饼图 / 各目录单元代码量），数据来自 `projectModules`。**唯一在根目录的页面**，资源引用是同级 | 改总览口径时 |
| [`html/`](html/) | **其余 26 个页面（4 分类页 + 22 模块页）**：资源引用一律 `../`（`../styles.css` / `../data/board.js` / `../vendor/` / `../charts/` / `../<page>.js`），指向入口写 `../index.html`，页面之间互链是同级文件名 | 新增 / 删除页面时 |
| [`html/agents.html`](html/agents.html) | **引擎模块页**（三节）：模块关系图 / 依赖关系 + 子单元代码量 / 各模块子单元条形图 | 改 engines 口径时 |
| [`styles.css`](styles.css) | 两页共用：令牌子集 + 骨架样式 + 组件配方（图表卡 / 表纸 / 空态） | 只在需要新版式零件时改，且先回登记 doodle-craft |
| [`agents.js`](agents.js) | 引擎页应用：读 `__BOARD__.engineModules`，渲染模块关系 / 依赖 / 子单元代码量 | 改引擎页时 |
| [`html/frontend.html`](html/frontend.html) · [`frontend.js`](frontend.js) | **前端页**（三节）：模块关系图 / 依赖 + 模块代码量 / 各模块单元代码量 | 改前端页时 |
| `html/frontend-<key>.html`（10）+ `html/backend-<key>.html`（12） · [`module.js`](module.js) | **模块页**（共 22 个，由 `tools/gen_module_pages.py` 按模板生成）：每个业务模块一个独立页面，三节与主页面同构 = 单元引用关系图 / 单元依赖（图·表 tab）+ 代码量饼图 / 单元三次对比；靠 `window.__MODULE_KEY__` + `window.__MODULE_SCOPE__`（frontend / backend）指定 | 改模块页时 |
| [`html/backend.html`](html/backend.html) · [`backend.js`](backend.js) | **后端页**（三节）：模块关系图 / 依赖 + 模块代码量 / 各模块单元代码量；数据来自 `backendModules` | 改后端页时 |
| [`html/ae-harness.html`](html/ae-harness.html) · [`ae-harness.js`](ae-harness.js) | **ae_harness 页**（三节）：架构关系图 / 左依赖图+右代码量卡片 / 每模块逐文件逐文件三次代码量 | 改 ae_harness 视图时 |
| `data/board.json` | 看板 + 智能体快照（机器可读） | **只由生成器写**，不手改 |
| `data/board.js` | 同一份快照的 `window.__BOARD__ = …` 形式（页面用） | **只由生成器写**，不手改 |
| `data/history.json` · `data/history.js` | 智能体模块量的历史快照（生成器追加，数值没变不追加，保留 60 次） | **只由生成器写**，不手改 |
| `tools/gen_board_data.py` | 生成器：扫仓库 → 写上面两个数据文件 | 改口径时改这里 |
| `tools/count_frontend.mjs` | 前端计数 + 模块间 `edges` + **单元间 `unitEdges`**（本地 TypeScript 语法树，无网络） | 只在前端计数口径变化时改 |
| `charts/` | **统一图表底层**：[`chart-framework.js`](charts/chart-framework.js)（生命周期 + 令牌 + `<viz-chart>`）、[`board-options.js`](charts/board-options.js)（纯函数 option）；契约见 [`charts/AGENTS.md`](charts/AGENTS.md) | 加图表时按契约改 |
| `vendor/vue.global.prod.js` | Vue 3.5.44 全局构建（本地化，离线可开） | 只有升级 Vue 时替换 |
| `vendor/echarts.min.js` | ECharts 5.6.0 **完整构建**（与 `frontend` 同源，本地化；依赖图 `graph` 只有完整构建才有） | 只有升级 ECharts 时替换 |
| [`README.md`](README.md) | 打开方式、已定 / 未定清单、指标口径表 | 每次方案推进后同步 |

## 指标口径（现行）

五个页面各自一套模块边界，**不可横向相加**。所有数字都由 `tools/gen_board_data.py` 生成，页面不重算。

| 页面 | 模块 = | 单元 = | 依赖 = |
| --- | --- | --- | --- |
| 总览 | 仓库一级目录（5 个工程目录） | 每个目录的第一层 | 目录间 Python import |
| 前端 | `frontend/src/modules/` 下 10 个业务目录 | 目录的第一层（.vue/.ts） | TS AST import |
| 后端 | `backend/apps/` 下 12 个 Django app | app 的第一层（.py） | app 间 Python import |
| 智能体 | `engines/` 下 6 个顶层目录 | 目录的第一层（.py） | 目录间 Python import |
| 原型链路 | `engines/ae_harness/` 下 7 个原语模块 + 外部装配方 | 模块内逐文件 | 包内跨组 import + 包外（backend_bridge / backend/apps）import |

依赖的统一口径：**一个文件对同一个目标（模块 / 组 / app）只计一次**，所以两个目标层级不同的页面（引擎页按顶层目录、ae_harness 页按组）算出来的数字不可互相套用。

通用定义：

- **代码行** = 非空物理行（前端 `.vue` 含 template/style）。
- **文件** = 代码文件数；排除 `__init__.py`、`__pycache__`、`migrations/`、`vendor/`、`logs/`。
- **历史对比** = 每次生成追加一条快照（数值没变不追加），页面取最近三次；缺的位显示「待记录」，不补零。
- **重新生成**：`python dev_docs/project-viz/tools/gen_board_data.py`；提交前用 `--check` 比对。

## 红线（违反即返工）

1. **不得冒充结论**：没有真实数据前，不画假图表、不填假数字、"待定"就写"待定"。占位卡片里的文字只说"这里将来放什么"。
2. **不得预设方案**：新增视图前，先在 README 写清目标（给谁看、回答什么问题）与**指标口径**；没有目标和口径就不加视图。
3. **视觉不自创**：配色 / 字号 / 间距 / 圆角 / 阴影 / 微倾一律取 doodle-craft 口径与 [`tokens.css`](../../frontend/src/shared/styles/tokens.css) 的值；`:root` 之外不写色值字面量，字号只取 7 档刻度，阴影模糊半径恒 0。
4. **不污染平台**：不 import `frontend/`、`backend/`、`engines/` 的代码，不调生产接口，不把本目录塞进任何构建链。
5. **断网可开**：页面不得依赖 CDN / 网络字体 / 远程脚本；新增依赖必须本地化进 `vendor/`。
6. **数据只读**：将来若读仓库文件或后端数据，一律只读；**禁止**把密钥、`.env`、数据库内容、用户数据写进 `data/` 或页面里。
7. **图表必须走统一底层**：任何图表都用 `<viz-chart>` + `charts/chart-framework.js`，**禁止**在页面里直接 `echarts.init`（契约与红线见 [`charts/AGENTS.md`](charts/AGENTS.md)）。

## 加一个视图的正确顺序

1. **定目标**：这张视图回答什么问题？（例：改一个模块会影响谁）
2. **定口径**：每个指标数什么、从哪取（静态快照走 `tools/gen_board_data.py`；**不调后端接口**），写进 README 的口径表再动手。
3. **选零件**：按 doodle-craft 的选型表取（指标 → 指标卡、列表 → 钉板卡、多行 → 表纸、无数据 → 空态），不自造。本目录已实现指标卡 `.kpi`、表纸 `.sheet-table`、钉板卡 `.ac-card`、空态 `.empty`；要别的零件从 [`standalone-html.md`](../../.agents/skills/doodle-craft/references/standalone-html.md) 抄进 `styles.css` 并登记。
4. **改代码**：加页面 → 在 `html/` 新建 `xxx.html` + 上一级新建 `xxx.js`（页面里资源写 `../`，复用 `../styles.css` 与 `../charts/`，侧栏两页同步），`styles.css` 只补缺的零件。
5. **自查**：`node --check overview.js frontend.js backend.js agents.js` + Playwright 打开**五个页面**截图（见下），确认零 console 错误、版式不裁剪。
6. **回写文档**：README 的「已定 / 未定」同步，方案变了就改，别留过期描述。

## 已知坑

- **`.gitignore` 例外有两条**：`!dev_docs/project-viz/index.html`（根入口）+ `!dev_docs/project-viz/html/*.html`（其余 26 页）。新增页面时不用再改 `.gitignore`，但位置只有两个：入口在根、其它都在 `html/`，否则会被 `dev_docs/**/*.html` 规则吃掉（`git check-ignore -v <路径>` 验一下）。
- **两套相对路径，别写混**：根入口 `index.html` 的资源写同级（`styles.css`、`data/board.js`、`vendor/`、`charts/`、`overview.js`），指向别的页面要带前缀（`html/frontend.html`）；`html/` 里的页面资源写 `../`，指向入口写 `../index.html`，页面之间互链写同级文件名。写错任何一边，`file://` 与 HTTP 都会白屏或 404。
- **静态服务要指到 project-viz 根**：`python -m http.server 8899 --directory dev_docs/project-viz`，入口是 `http://127.0.0.1:8899/index.html`；`--directory` 指到 `html/` 会让 `../` 资源全部 404，指到别处则打不开入口。
- **纵向滚动在内层**：滚动条落在 `.main__body`（`flex: 1 1 0; min-height: 0; overflow-y: auto`）。截图脚本滚 `window` 是滚不动的，要 `document.querySelector('.main__body').scrollTop = y`。
- **Vue 模板写在 HTML 里**：用的是带编译器的全局构建，所以 `vendor/` 里必须是 `vue.global.prod.js`；换成 `vue.runtime.global.prod.js` 会白屏。
- **不能 `fetch` 本地数据**：页面是 `file://` 打开的，`fetch('data/board.json')` 会被 CORS 拦掉。所以生成器额外写一份 `data/board.js`（`window.__BOARD__ = …`），用 `<script>` 引入。
- **快照会过期**：代码一改，看板数字就旧了。提交前跑 `python dev_docs/project-viz/tools/gen_board_data.py --check`（有差异退出码 1）。
- **口径要三处同步**：`tools/gen_board_data.py` 的模块 docstring、页面第 2 节、README 的口径表——改一处就要改全，否则数字和解释打架。
- **数字要能解释**：看板上的每个数都能追到生成器里的某段口径；解释不了的数字宁可不上表。
- **侧栏是"分组 + 链接"，且每页一份**：`视图`（总览）+ `前端` / `后端` / `引擎` / `ae_harness` 四组各一项。跨页链接按两套目录生成（入口页带 `html/` 前缀，`html/` 内页面指向入口用 `../index.html`，其余同级）；看板页内用 `#锚点`。因为页头吸顶，`.doc-section` 必须带 `scroll-margin-top: calc(var(--app-topbar-h) + var(--app-space-md))`，否则跳过去标题被页头盖住（踩过）。
- **侧栏是手写六遍的**：`index.html`（根）+ `html/frontend.html` / `html/backend.html` / `html/agents.html` / `html/ae-harness.html` + 模块页模板，各一份；改导航（增删条目、改文案）必须全部同步，漏一个就会出现"某页点不动"。用 `tools/sync_sidebar.py` 刷，别手抄。
- **每个页面都是独立的三节看板，没有全局分类筛选**：筛选是旧的明细看板才有的概念，已随该页删除。要加内容就加在对应页面的三节里。
- **引擎视图的数据在 `board.json` 的 `engineModules` 键下**（目录分组 + 每模块 label/note/units/relations/totalTrend + `agentsDoc`），由 `collect_engine_modules()` 生成；`agents` 键是已退役的 `engines/agents` 留下的空骨架（`groups: []`），页面已不读它，别把两者混成一份。历史快照在 `data/history.json`。
- **依赖图是静态的**：`engineModules.relations` 来自 AST 的 `import`，只证明"模块引用了谁"，**不证明运行期谁调谁**；页面已写明这句话，别在文案里把它说成调用链。它同时是第 1 节图的边来源。
- **frontend 页（`frontend.html`）的「模块」= `frontend/src/modules/` 下 10 个业务目录**：共享层（`shared/`+`views/`+`router.ts`）不是业务模块，统计里不算，但**架构图上要画一个灰色虚框节点**——10 个模块都依赖它，不画就会变成 10 个孤立点。指向共享层的边在图上用虚线，表里也列出（标记 `shared`）。
- **模块页的三节必须与主页面同构**：① 单元引用关系图（自绘 SVG，椭圆布局，点节点高亮）② 单元依赖（图/表 tab）+ 代码量饼图 ③ 单元三次对比。**不要**做成"饼图+明细表+柱"那套——结构不同用户会怀疑是不是同一个 skill 做的（踩过，返工一次）。
- **模块页同时服务前端与后端**：同一份模板 + `module.js`，靠 `window.__MODULE_SCOPE__` 切数据键（`frontendModules` / `backendModules`）；路径前缀也随之变（`frontend/src/modules/` / `backend/apps/`）。新增 scope 要同时改 `module.js` 的 `SECTION`/`ROOT_LABEL` 与 `tools/gen_module_pages.py` 的 `GROUPS`。
- **后端单元边支持两种 import 写法**：相对导入（`from .models import`）与绝对导入（`from backend.apps.<app>.<rest> import`），解析在生成器 `_unit_import_edges()`；**只认本 app 前缀**，`backend.apps.ai_assistant.*` 这种跨 app 引用不算单元边。12 个 app 合计 126 条（task_list 33 / ai_assistant 29 / case_manager 19 / device_pool 13）。
- **节点数多时节点宽与字号要缩**：单元 > 16 个时节点宽 92px、字号 9px（`task_list` 21 个单元），否则 150px 宽会在椭圆上叠起来。**字号必须用 inline style**——SVG 的 `font-size` 呈现属性会被 CSS 的 `.dep-node__title { font-size }` 覆盖（踩过，改了属性没生效）。
- **单元间引用来自 `count_frontend.mjs` 的 `unitEdges`**：TS AST 解析 import，把目标路径映射到"单元"（模块内相对路径第一段）；**只算模块内部**，跨模块与 `shared` 不计入。10 个模块合计 261 条边（ai-assistant 50 / ops-console 37 / serial-log 37 / knowledge-search 37）。
- **单元关系图用椭圆布局 + 曲线**：单元数 5~11、边 3~22，手工坐标不可维护，所以按椭圆均匀分布；边用二次贝塞尔（控制点沿法线交替偏移），否则 22 条线全穿圆心堆成一团；**标签只在选中节点时显示**且按 `index % 4` 错开位置，否则同一节点的多条边数字会叠在一起。
- **前端每个业务模块是一个独立页面**：`html/frontend-<key>.html`（10 个），共用 `module.js`，靠页面里一行 `window.__MODULE_KEY__ = "<key>"` 区分；**不要再改回 hash 切面**（试过，用户明确要独立页）。模板与生成脚本在 `tools/module-page.template.html` + `tools/gen_module_pages.py`，模块增减时跑一次脚本重新生成（旧页面要手动删）。
- **5 个主页面 + 模板的侧栏都列 10 个前端模块项**：`.sidebar__nav-item--sub`（缩进 + 小字号），指向 `frontend-<key>.html`；模块清单由 [`tools/sync_sidebar.py`](tools/sync_sidebar.py)（读 `data/board.json`）统一刷 6 处侧栏，别手抄。
- **前端模块名就是目录名，没有中文名**：生成器里 `label` 留空，否则卡片会显示「workflow workflow」。
- **依赖图边宽要限幅**：`width: min(4, 0.8 + count * 0.12)`——共享层那条 40 次的边会把图糊成一把扇子。
- **backend 页（`backend.html`）的「模块」= `backend/apps/` 下 12 个 Django app**：写在生成器 `BACKEND_MODULES`；单元口径与 engines 页一致（app 下的直接子目录整体算一个、直接 .py 各算一个，排除 `__init__.py`/`migrations/`）；`config`/`gateway`/`shared` 属基础设施，不计入跨模块关系。
- **第 2 节必须有「模块依赖图 / import 关系」两个 tab**：agents 页与 backend 页都曾被删成只有表（同一个错误犯两次）。第 1 节的图看结构、第 2 节的图看次数，不是重复，不许省。
- **第 2 节左栏 import 用表格、右栏模块代码量用饼图**：`import 次数表` tab 是 `.sheet-table` 三列（被调用方 / 调用方 / import 次数），**不要做成卡片**——两列数据逐行比较时表格的列对齐更好扫，卡片会把 8 条以后压成横带（踩过：做成卡片后用户反馈「效果不行」）。右栏是 `BoardOptions.modulePie()` 饼图，空心占外半径 **30%**（`radius: ["20.4%", "68%"]`；legend 带行数、tooltip 带百分比）。三页（agents / backend / frontend）保持一致。
- **依赖图的箭头也是数据流方向**：`graphOption` 里 links 要反转成 `{ from: 被调用方, to: 调用方 }`，与卡片同向；第 1 节的架构图仍保持 import 方向（它是人工语义图）。
- **渐变文字要收窄区间**：给文字做 `background-clip: text` 渐变时，用 `shadePair()` 的 `deep(L36) → mid(L52)`，**不要到 light(L78)**——末端太浅，小字号（≤14px）下几乎看不见。
- **改样式前先查重**：同一个类名累积过三份规则（如曾经的 `.rel-card` 一行版 / 两行版 / 单行版），后写的旧规则会覆盖新样式，页面上看到的和写的完全不一样。加规则前先 `Select-String "^\.<类名前缀>"` 数一遍。
- **节点多时 depGraph 要传 positions**：`depGraph(nodes, edges, theme, { positions })` 复用架构图分层坐标；不传时退回 circular，12 个节点会挤成一团。
- **超长模块名不显示中文名**：`knowledge_search` / `report_generator` 这类名字会把「单元数/行数」挤开，用 `shortLabel`（>14 字符留空）而不是加宽列。
- **engines 页（`agents.html`）的「模块」= `engines/` 下 6 个顶层目录**：`ae_harness` / `backend_bridge` / `device` / `uart_log` / `utils` / `vision`，写在生成器 `ENGINE_MODULES`（`engines/agents` 已退役，不要加回来）。
- **子单元只统计一层，不再往里拆**：单元 = 模块下的**直接子目录**（递归汇总其中全部 `.py`，整体算一个）或**直接 `.py` 文件**（各算一个）；排除 `__init__.py`、`__pycache__`、`logs/`。例如 `ae_harness` 只算 7 个单元（7 个直接子目录），不深入 `agents/models.py` 那一层；`backend_bridge` 9 个、`device` 5 个。口径在 `collect_engine_modules()`。
- **两页的三节标题都带序号**：`1. …` / `2. …` / `3. …`，第 1 节不许缺序号（两页要一致）。
- **页面结构照 ae_harness 三节**：① 自绘 SVG 模块关系图（点节点高亮相关线，节点右下角有 `AGENTS` 入口）② 左 tab（模块依赖图 / import 次数表）+ 右侧 6 张子单元代码量卡片 ③ 每模块一张**三系列竖柱状图**（`BoardOptions.unitTrendColumn`：本次 / 最近一次 / 最近两次），两列网格。
- **第 3 节要带对比**：每个单元一组柱（`unit.trend = [n, n-1, n-2]`），模块总量也挂在 `module.totalTrend` 上显示三张卡；历史里缺的位显示「待记录」，不补零。单元 > 10 个的模块加 `.cmp--wide` 独占一行，否则 X 轴标签会挤成一团。
- **单元多时柱顶数字要收敛**：`unitColumn` 里 `label.show = rows.length <= 10`，否则 17 个单元的数字会互相压（`task_list` 21 个单元就踩过）。
- **markdown 渲染是共享文件**：`markdown.js` 暴露 `window.SimpleMarkdown.render`，ae_harness 页与 agents 页的 AGENTS.md 弹层都用它；不要在某个页面里再复制一份。
- **ae_harness 的「模块」就是根目录的七个文件夹**：`agents`（创建智能体）/ `tools`（智能体工具箱）/ `knowledge`（知识检索）/ `assistant`（运行骨架）/ `workflow`（工作流）/ `event`（智能体事件）/ `middleware`（观测中间件），写在生成器 `AE_HARNESS_GROUPS`，顺序即页面顺序；**不要**再合并成桶或另立分层概念（曾经做过"角色/入口"合并与"五层"，都被推翻了）。新增顶层目录时要同步：`AE_HARNESS_GROUPS`、`AE_HARNESS_WHY`、页面 `MODULE_ORDER`、`tokens().colors`（`charts/chart-framework.js`）、`DIAGRAM_LAYOUT`（`knowledge` 就是按这套加的）。
- **本包只出原语，装配在包外**：`assistant/` 现在只剩 `_bootstrap.py`（运行时骨架），控制台的单智能体与 SOP 入口已删除；平台侧装配在 `engines/backend_bridge/`，`backend/apps` 也直接引用部分原语。所以图上是「外部装配方 → 7 个原语模块」+ 包内唯一的 `workflow → event`，**不要**再把 assistant 画成装配中心。
- **middleware 是「观测/控制件」不是「调用链环节」**：由 `backend_bridge` 以 `ObservationMiddleware` / `CancelMiddleware` 注入到 `create_agent(observers=...)`，只读 hook，不改行为、不落盘；包内没有模块引用它，所以图上它的线来自外部装配方。
- **删样式只能按类名精确删，禁止按注释区间删**：曾经用「从 A 注释删到 B 注释」清理死 CSS，把中间仍在用的 `.dep-*` / `.mod-total*` / `.cmp*` / `.module-stat*` 一起删掉，页面变成黑块 + 竖排文字。删完必须用 Playwright 量一遍关键元素的 `getComputedStyle`（display / grid 列 / fill），不能只看 DOM 存在。
- **ae_harness 页面固定三节**：① 架构（模块关系图，点模块高亮）② **左依赖关系（tab 切图/表）+ 右模块代码量卡片**（同一节并排）③ 各模块代码量（**两列网格**，每模块一张分组柱 + 三张卡，窄屏落回单列）。
- **第 2 节两栏比例 `1.2fr / 1.15fr`（min 420px）**：右栏卡片 551×77，与左栏（图 400 + tab ≈ 590）高度接近；卡片内边距 `--app-space-lg`，别改回 sm（会扁成 53px）。
- **依赖图节点标签在下方**：`depGraph(..., { labelPosition: "bottom" })`——`right` 在容器变窄时文字会压在圆点上；这个选项默认 `right`，别影响 agents 页。
- **第 2 节左栏是图/表互斥**：`depTab` 为 `graph | table`，用 `v-if` 切（不是 `v-show`——ECharts 在 0 宽容器里 init 会算出错误尺寸，切回来必须重新挂载）。不要往回加 KPI 卡、分层卡、文件清单、点击档案面板等其它区块。
- **代码量右栏是「一行三值」卡片**：`模块名｜文件数｜行数` 三块**主体同字号（22px）、同基线、同一水平线**，中文名与单位统一 12px 作后缀。做法：卡片用 `grid` + `align-items: baseline`，每块内部 `flex` + `align-items: baseline`，主体元素 `flex: 0 0 auto`（否则会被挤成省略号）。
- **不要用 SVG 文字画数字**：SVG 是替换元素，`align-items: baseline` 对不齐，会让人觉得"模块名偏下"（踩过）。数字渐变用 CSS `background-image: linear-gradient(<深hex>, <浅hex>)` + `background-clip: text`，深浅由 `shadePair()` 按 HSL 算（保留色相、深端 L36% / 浅端 L78%）；**不要**用 `color-mix()` 当渐变停点（Chromium 计算值正确但绘制不出来）。
- **同类样式只留一份**：给同一类新增规则前先 `Select-String` 查重；重复块里旧值会覆盖新值（`.code-card__svg` 曾出现 width 100% 与 110px 两份，导致数字被拉到 60px）。2026-11 已把 `styles.css` 按 selector 合并去重一次（2228 → 1892 行，顶层重复 0），之后再追加新块要接着用**同一条规则**，别另起一条。
- **批量替换必须限定位置**：`str.replace` 会替换**所有**匹配；曾把 `bar()` 与 `fileTrendBar()` 里相同的 `rows.map(...)` 一起改掉，`bar()` 里没有 `opts` 变量，直接 `ReferenceError` 让 board.html 白屏。改共享函数里的重复片段要按行号或加足够上下文。
- **第 3 节两列**：`.cmp-list` 是 `repeat(2, minmax(0,1fr))`，卡片内三张统计卡用 `1fr` 均分；x 轴文件名走 `fileTrendBar(..., { labelOf })` 保留完整名（去掉 `.py`），不要再退回 `shortName` 的 16 字符截断。
- **验证要用 HTTP 打开**：`python -m http.server 8899 --directory dev_docs/project-viz` 再访问 `http://127.0.0.1:8899/index.html`，`file://` 下 `<link>` 的 CSS 会被缓存，改完样式仍看到旧渲染（曾因此误判"样式没生效"）。
- **交互只有一种：点模块 → 相关调用线统一变绿**（`--c-device`，3px 实线 + 绿色箭头），再点同一个取消；**默认状态零变化**（不淡化、不预高亮）。不要再加场景切换按钮——"创建 assistant / 创建工作流"两个 tab 已被移除。
- **每个模块节点右下角（内部）有 `AGENTS` 入口**：位置 `translate(x + w - 54, y + h - 16)`、52×14 的圆角小条，**必须在节点 `<g>` 之后渲染**（先渲染会被节点的 rect 盖住，踩过）。点击弹出该模块目录下的 `AGENTS.md`（`engines/ae_harness/<key>/AGENTS.md`）。文档由生成器读进 `ae_harness.groups[].agentsDoc` 写进快照（**不要**在页面里 fetch，file:// 会被 CORS 拦），页面用 `renderMarkdown()` 渲染（自带极简解析：标题/有序无序列表/表格/代码块/引用/粗体/行内码）。没有 `AGENTS.md` 的模块不显示按钮（当前 7 个模块都有，`logs/` 不算模块）。弹层支持点遮罩、点「关闭」、按 ESC 三种关法。
- **第 1 节只有标题 + 图**（模块节点上的 AGENTS 入口属于图的一部分，不算文字说明）：标题是「AE Harness 模块架构：模块关系」，标题与图之间不放 hint、依据、图注。改这里别再把说明文字加回来。
- **架构图只有两种线**：外部装配方 → 各原语模块（竖直线，从顶部那条虚线框底边落到目标节点顶边中点，标签写「N 处引用」）；包内跨组（目前只有 `workflow → event`，横线）。点中某个节点后，与它相连的线统一转绿实线 3px（箭头也换绿色 marker），再点取消。
- **布线靠 `routeEdge(from, to)`，不写死坐标**：同一行 → 横线；`from.key === "external"` → 竖直落到目标顶边中点；其余走中缝的直角折线。第二行的竖线走第一行两个节点之间的空档，所以 `DIAGRAM_LAYOUT` 里第二行节点的 cx 必须落在第一行的空隙上，否则线会穿过节点。
- **`DIAGRAM_LAYOUT` 的坐标是试出来的**：外层一条 `external`（全宽虚线框 y=40）、第一行 agents/tools/knowledge/assistant（y=180）、第二行 workflow/event/middleware（y=340）；改任何一个节点都要重新看一遍线和标签，别再退回贝塞尔手调。
- **布线按 archify 的规范正交汇制**（参考 `.agents/skills/archify`）：端口只从节点边中点出；折线拐角 8px 圆角（`orthPath()`）；标签贴着自己的线段，不压节点、不压其它线。
- **图上的边不许手写**：边的两端与次数来自生成器（`ae_harness.external.edges` + `ae_harness.relations`），页面只用 `routeEdge()` 算折线。要改图先改代码，再让生成器算出来——手写一条数据里不存在的边就违反红线第 1 条。
- **符号名进表、数字进图**：图上标签只写「N 处引用」（线段太窄，放不下符号）；真实符号（`create_agent()` / `ObservationMiddleware` / `run_sop()` …）列在第 2 节的「外部装配方」表里，由生成器从 AST 的 import 语句里抽。
- **SVG 的 viewBox 必须写静态属性**：in-DOM 模板里 `:viewBox` 会被浏览器小写成 `viewbox`，SVG 拿不到视口就按 1:1 像素绘制，节点会被画到容器外（曾经整块图跑出画面）。固定尺寸的图直接写 `viewBox="0 0 1180 460"` + CSS `aspect-ratio: 1180 / 460` 同比例。
- **依赖图的方块是 SVG，不是图表**：节点坐标写死在 `ae-harness.js` 的 `DIAGRAM_LAYOUT`；这属于示意图，不走 `charts/` 的 ECharts 通道，也不要往 `<viz-chart>` 里塞。
- **跨组引用的「为什么」是人工写的**：`AE_HARNESS_WHY`（生成器顶部）按 `引用方->被引用方` 给一句因果；import 只能证明引用了，不能证明原因。新增跨组引用时若没补这句，页面会显示「（未写人工说明）」——宁可留白也不要编。
- **ae_harness 的对比记录靠历史累积**：`history.json` 每条含 `ae_harness.{groups,files}` 行数；页面「模块对比记录」取最近三次，缺的显示「待记录」，**禁止补零或倒推**；新增组要同时确认 `_ae_comparison()` 能覆盖到。
- **目录名统一写成「<中文>模块：<目录名>」**（如 `工作流模块：workflow`）：中文名在 `agents.js` 的 `GROUP_TITLES` 一处维护，Tab、图表 y 轴、功能模块说明三处共用；新增目录必须补中文名，否则会退回裸目录名。
- **「结构示意」不是界面截图**：前端页第 5 层的页头/KPI/筛选/表格块，是按模板里出现过哪类组件 + 固定块序推断的**结构**，页面已写明；不要把它当真实 UI，也不要拿它替代截图。
- **页面 = 模块下非 components 的 .vue**：`components/` 里的是子组件（39 个），不计入页面数；统计口径写在 `collect_frontend_pages()`。
- **接口提取依赖 api-client 别名**：`client` / `djangoClient` 等别名不统一，采集器先解析 `import X from "@/shared/api-client"` 再按别名抓 `X.get(...)`；新增别名无需改代码，但直接 `fetch()` 的调用抓不到。
- **`v-else` 只能有一个**：`agents.html` 曾把三个 `<section>` 都写成 `v-else`，Vue 报 `compiler-30` 整页白屏。多个兄弟块要共享条件时，用一个容器包起来（`<div v-else>…</div>`），或改用 `v-if`。
- **总览 = 仓库一级目录的三节看板**（不再是"只放数字不画图"的结论页）：模块 = `backend` / `engines` / `frontend` / `tests` / `utils`，单元 = 每个目录的第一层（子目录整体算一个、代码文件各算一个），口径在 `collect_project_modules()`。
- **前端 → 后端是 HTTP 调用，不是 import**：总览里 `frontend → backend` 那条边来自 `count_frontend.mjs` 采集的 api-client 调用（95 次 / 71 条路径），`kind: "http"`，图上用**橙色虚线**、「处」作量词，与紫色 import 边区分；表里多一列「类型」。图下方有图注说明两种虚线的含义——**图例必须写清**，否则用户会以为那是 import。
- **「怎么连接的」看接口明细表**：第 2 节主表下方挂一张「前端 → 后端：接口调用明细」（`http.byApp`），按 URL 前缀归到后端 app（`/cases` → case_manager 等，人工对照 `backend/apps/*/urls.py`，映射表在生成器 `HTTP_API_APPS`）。只连一条线不解决问题——用户要的是"前端调了哪些后端接口"。
- **总览排除的目录要写清**：缓存（`.ruff_cache` / `.mypy_cache` / `__pycache__`）、临时（`temps` / `.pytest-tmp` / `.testtmp` / 时间戳目录）、第三方资产（`.agents/skills`，14 万行）、文档（`dev_docs`，含本看板自身）、运行数据（`data`）都不计入；新增排除项要同时改 `PROJECT_SKIP_DIRS` 与页面说明。
- **历史趋势要靠时间攒**：`history.json` 只在数值变化时追加一条，`--check` 不写盘；不足 2 条时页面显示空态而不是画一个点——别为了"好看"塞假历史。

## 自检（改完跑一遍）

```bash
node --check dev_docs/project-viz/overview.js
node --check dev_docs/project-viz/frontend.js
node --check dev_docs/project-viz/backend.js
node --check dev_docs/project-viz/agents.js
node --check dev_docs/project-viz/ae-harness.js
node --check dev_docs/project-viz/module.js
python dev_docs/project-viz/tools/gen_board_data.py --check   # 快照与代码一致
python -m http.server 8811 --directory dev_docs/project-viz   # 入口 http://127.0.0.1:8811/index.html（或直接双击根目录 index.html）
```

```
[ ] 无 console / pageerror
[ ] 版式不裁剪：缩小窗口，正文仍只在 .main__body 内滚动
[ ] 令牌：色值全 var(--…)、字号/间距/圆角/阴影取刻度、阴影无模糊
[ ] 卡片有微倾且 hover 回正；动 transform 的类有 prefers-reduced-motion 降级
[ ] "待定"与"已定"和 README 一致，没有假数据
```
