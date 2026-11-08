# project-viz AGENTS.md

> 层级：根 [`AGENTS.md`](../../AGENTS.md) → **本文件**。本文件只约束 `dev_docs/project-viz/`，不改平台代码；与上级冲突时以上级为准。

## 这个目录为什么存在

**一句话**：把**当前这个仓库**可视化出来——让人不用翻代码就能看懂"有哪些模块、谁依赖谁、一次任务怎么跑"。

几条创建时的判断，避免以后被误解：

1. **它是文档级产物，不是平台功能。** 放 `dev_docs/` 而不是 `frontend/`：不进 Vite 构建、不接后端接口、不参与 CI 门禁。任何 clone 下来的人双击 `index.html` 就能看，不需要装 Node、不需要起服务。
2. **它是五个页面。** ①「总览」= **结论页**（领域打通率 / 引擎能力 / 健康分 / 最近变化 + 领域矩阵，**刻意不画图表**）；②「明细看板」（三层模块量 + 五张明细图）；③④⑤「前端 / 后端 / 智能体功能模块」——每个都是**五层**（数据总览 / 依赖关系 / 流程时序 / 功能模块说明 / 历史趋势）。五页**不共享视图层**（各自一份侧栏与页头、各自的 js），只共享 `styles.css`、数据快照与 `charts/`。数据都是**静态快照**（`tools/gen_board_data.py` 生成），流程时序与历史趋势的"数据性质"见下文。依赖关系 / 时序 / 趋势仍未定，别当成"方案已定"。
3. **它用 Vue，但不打包。** 选 Vue 是为了后续视图（关系图 / 时序 / 过滤交互）写起来比手写 DOM 省事；`vendor/vue.global.prod.js` 是本地化的 Vue 3 全局构建，保证断网可开。
4. **视觉沿用平台默认。** 用 [doodle-craft](../../.agents/skills/doodle-craft/SKILL.md) 的纸面 + 粗线 + 硬影 + 微倾，不另造一套风格——这页代表的是这个仓的既有视觉。

## 目录职责

| 路径 | 职责 | 谁改 |
| --- | --- | --- |
| [`index.html`](index.html) | **总览（首页）**：一句话结论 + 4 个北向 KPI + 领域矩阵 + 健康分 + 变化 + 下钻入口 | 改结论口径时 |
| [`board.html`](board.html) | **明细看板**：三层模块量 + 五张明细图（`app.js` 由它加载） | 改看板时 |
| [`agents.html`](agents.html) | **页面二 · 智能体功能模块**（独立页面，自己一份侧栏与页头，无分类筛选） | 改引擎模块清单时 |
| [`styles.css`](styles.css) | 两页共用：令牌子集 + 骨架样式 + 组件配方（图表卡 / 表纸 / 空态） | 只在需要新版式零件时改，且先回登记 doodle-craft |
| [`app.js`](app.js) | 明细看板的应用：读 `window.__BOARD__`、渲染图表 | 改看板时 |
| [`overview.js`](overview.js) | 总览页应用：只读 `__BOARD__.overview`，不放图表 | 改总览时 |
| `tools/domains.json` | **业务域对照表（唯一人工输入）**：10 个域 → 前端模块 / 后端 App / 引擎目录 / direct·via·none | 域变更时手改 |
| [`agents.js`](agents.js) | 引擎页应用：读 `__BOARD__.agents` / `__HISTORY__` / `__FLOW__`，渲染五层 | 改引擎页时 |
| [`frontend.html`](frontend.html) · [`frontend.js`](frontend.js) | **前端页**（五层：模块行 / 路由 / 依赖 / 流程 / 趋势） | 改前端页时 |
| [`backend.html`](backend.html) · [`backend.js`](backend.js) | **后端页**（五层：App 行 / 文件构成 / 依赖 / 流程 / 趋势） | 改后端页时 |
| `data/board.json` | 看板 + 智能体快照（机器可读） | **只由生成器写**，不手改 |
| `data/board.js` | 同一份快照的 `window.__BOARD__ = …` 形式（页面用） | **只由生成器写**，不手改 |
| `data/history.json` · `data/history.js` | 智能体模块量的历史快照（生成器追加，数值没变不追加，保留 60 次） | **只由生成器写**，不手改 |
| `data/flow.js` · `flow-frontend.js` · `flow-backend.js` | 三层各自的流程 / 时序（**人工维护**，每步带 source 与 caveat） | 改流程时手工同步 |
| `tools/gen_board_data.py` | 生成器：扫仓库 → 写上面两个数据文件 | 改口径时改这里 |
| `tools/count_frontend.mjs` | 前端计数（本地 TypeScript 语法树，无网络） | 只在前端计数口径变化时改 |
| `charts/` | **统一图表底层**：[`chart-framework.js`](charts/chart-framework.js)（生命周期 + 令牌 + `<viz-chart>`）、[`board-options.js`](charts/board-options.js)（纯函数 option）；契约见 [`charts/AGENTS.md`](charts/AGENTS.md) | 加图表时按契约改 |
| `vendor/vue.global.prod.js` | Vue 3.5.44 全局构建（本地化，离线可开） | 只有升级 Vue 时替换 |
| `vendor/echarts.min.js` | ECharts 5.6.0 **完整构建**（与 `frontend` 同源，本地化；依赖图 `graph` 只有完整构建才有） | 只有升级 ECharts 时替换 |
| [`README.md`](README.md) | 打开方式、已定 / 未定清单、指标口径表 | 每次方案推进后同步 |

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
4. **改代码**：加在看板 → `app.js` + `index.html` 分区；加独立页面 → 新建 `xxx.html` + `xxx.js`（复用 `styles.css` 与 `charts/`，侧栏两页同步），`styles.css` 只补缺的零件。
5. **自查**：`node --check app.js overview.js frontend.js backend.js agents.js` + Playwright 打开**五个页面**截图（见下），确认零 console 错误、版式不裁剪。
6. **回写文档**：README 的「已定 / 未定」同步，方案变了就改，别留过期描述。

## 已知坑

- **`.gitignore:127`（`dev_docs/**/*.html`）会忽略五个页面**（`index.html` / `board.html` / `frontend.html` / `backend.html` / `agents.html`）：页面只在本地生效，`css/js/md` 会入库。要入库需在 `.gitignore` 加例外（`!dev_docs/project-viz/*.html`）——这是待决策项，别默默改。
- **纵向滚动在内层**：滚动条落在 `.main__body`（`flex: 1 1 0; min-height: 0; overflow-y: auto`）。截图脚本滚 `window` 是滚不动的，要 `document.querySelector('.main__body').scrollTop = y`。
- **Vue 模板写在 HTML 里**：用的是带编译器的全局构建，所以 `vendor/` 里必须是 `vue.global.prod.js`；换成 `vue.runtime.global.prod.js` 会白屏。
- **不能 `fetch` 本地数据**：页面是 `file://` 打开的，`fetch('data/board.json')` 会被 CORS 拦掉。所以生成器额外写一份 `data/board.js`（`window.__BOARD__ = …`），用 `<script>` 引入。
- **快照会过期**：代码一改，看板数字就旧了。提交前跑 `python dev_docs/project-viz/tools/gen_board_data.py --check`（有差异退出码 1）。
- **口径要三处同步**：`tools/gen_board_data.py` 的模块 docstring、页面第 2 节、README 的口径表——改一处就要改全，否则数字和解释打架。
- **数字要能解释**：看板上的每个数都能追到生成器里的某段口径；解释不了的数字宁可不上表。
- **侧栏是"分组 + 链接"，且每页一份**：`视图`（项目看板 / 口径 / 下一步）+ `引擎`（智能体功能模块）。看板页内用 `#锚点`，跨页用 `agents.html` / `index.html`；因为页头吸顶，`.doc-section` 必须带 `scroll-margin-top: calc(var(--app-topbar-h) + var(--app-space-md))`，否则跳过去标题被页头盖住（踩过）。
- **五个页面的侧栏是手写五遍的**：`index.html` / `board.html` / `frontend.html` / `backend.html` / `agents.html` 各一份，改导航（增删条目、改文案）必须四处同步改，漏一个就会出现"某页点不动"。这是拆页的代价；若嫌烦，可另立变更抽成 `nav.js` 统一渲染（但那就等于共享视图层，需先定）。
- **智能体页是独立页面，不是看板的一个分区**：它没有分类筛选（那是看板全局状态），也不要给它加 `<section>` 式的兄弟分区——要加内容就加在 `agents.html` 里。
- **引擎视图的数据也在 `board.json`**：`agents` 键下（目录分组 + 每模块类型/功能/条目/类/方法/行数/测试 + `imports` 依赖边），由同一个 `gen_board_data.py` 生成；历史快照在 `data/history.json`、流程在 `data/flow.js`，别把三者混成一份。
- **依赖图是静态的**：`agents.imports` 来自 AST 的 `import`，只证明"模块引用了谁"，**不证明运行期谁调谁**；页面已写明这句话，别在文案里把它说成调用链。
- **流程时序是人工维护的**：`data/flow.js` 每步都带 `source` 与全局 `caveat`；工作流结构变了要手工同步（没有生成器能替你验证顺序）。宁可不画，也不要从代码猜一个看起来对的时序。
- **目录名统一写成「<中文>模块：<目录名>」**（如 `工作流模块：workflow`）：中文名在 `agents.js` 的 `GROUP_TITLES` 一处维护，Tab、图表 y 轴、功能模块说明三处共用；新增目录必须补中文名，否则会退回裸目录名。
- **「结构示意」不是界面截图**：前端页第 5 层的页头/KPI/筛选/表格块，是按模板里出现过哪类组件 + 固定块序推断的**结构**，页面已写明；不要把它当真实 UI，也不要拿它替代截图。
- **页面 = 模块下非 components 的 .vue**：`components/` 里的是子组件（39 个），不计入页面数；统计口径写在 `collect_frontend_pages()`。
- **接口提取依赖 api-client 别名**：`client` / `djangoClient` 等别名不统一，采集器先解析 `import X from "@/shared/api-client"` 再按别名抓 `X.get(...)`；新增别名无需改代码，但直接 `fetch()` 的调用抓不到。
- **长表用目录 Tab 切，不要堆叠**：智能体页的数据总览把 9 个目录做成一排 tab（`.tabbar` / `.tab`），一次只渲染一个目录的模块 + 小计；再往表里加列之前，先确认单个 tab 里的表格还看得完。
- **总览不画图**：结论页只放数字、矩阵与分数条；图表一律留在明细页。想加图先问"它回答的是结论还是证据"。
- **健康分只有一个真相源**：权重与扣分常量写在 `gen_board_data.py`（`HEALTH_WEIGHTS` / `*_PENALTY`），页面只显示；改权重不要改页面。
- **领域对照表是人工判断**：`tools/domains.json` 的 `coverage`（direct / via / none）没有代码可以自动判定，改它等于改结论，务必写清 `note`。
- **历史趋势要靠时间攒**：`history.json` 只在数值变化时追加一条，`--check` 不写盘；不足 2 条时页面显示空态而不是画一个点——别为了"好看"塞假历史。

## 自检（改完跑一遍）

```bash
node --check dev_docs/project-viz/app.js
node --check dev_docs/project-viz/overview.js
node --check dev_docs/project-viz/frontend.js
node --check dev_docs/project-viz/backend.js
node --check dev_docs/project-viz/agents.js
python -m http.server 8811 --directory dev_docs/project-viz   # 或直接双击 index / board / frontend / backend / agents.html
```

```
[ ] 无 console / pageerror
[ ] 版式不裁剪：缩小窗口，正文仍只在 .main__body 内滚动
[ ] 令牌：色值全 var(--…)、字号/间距/圆角/阴影取刻度、阴影无模糊
[ ] 卡片有微倾且 hover 回正；动 transform 的类有 prefers-reduced-motion 降级
[ ] "待定"与"已定"和 README 一致，没有假数据
```
