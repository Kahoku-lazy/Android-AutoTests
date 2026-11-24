# 项目可视化

把**这个仓库**画出来：有哪些模块、谁依赖谁、每块多少代码。静态快照、免构建、断网可开。

数据由 [`tools/gen_board_data.py`](tools/gen_board_data.py) 扫描生成，页面只读快照，不调任何接口。

## 打开

直接双击根目录的 [`index.html`](index.html)（入口），或起一个本地服务（推荐，避免浏览器缓存 CSS）：

```bash
python -m http.server 8811 --directory dev_docs/project-viz
# http://127.0.0.1:8811/index.html
```

**入口页在项目根，其余 26 个页面在 [`html/`](html/)**：入口页的资源引用是同级（`styles.css` / `data/` …），其余页面的资源引用是 `../`；侧栏链接已按两套目录分别生成。

页面清单：

- [index.html](index.html) —— **入口 / 总览**：1.1 平台架构（运行时组件与调用链）+ 1.2 实际代码依赖（仓库一级目录的 import 次数）
- [html/frontend.html](html/frontend.html) —— **前端**：`frontend/src/modules/` 下 10 个业务目录
- **22 个模块页**（都在 `html/`）—— 前端 10 个（如 [html/frontend-ops-console.html](html/frontend-ops-console.html)）+ 后端 12 个（如 [html/backend-task_list.html](html/backend-task_list.html)），每个业务模块一页，三节与主页面同构：单元引用关系图 / 单元依赖（图+表）+ 代码量饼图 / 单元三次对比
- [html/backend.html](html/backend.html) —— **后端**：`backend/apps/` 下 12 个 Django app
- [html/agents.html](html/agents.html) —— **引擎**：`engines/` 下 6 个顶层目录
- [html/ae-harness.html](html/ae-harness.html) —— **原型链路**：`engines/ae_harness/` 下 7 个原语模块 + 一条「外部装配方」

## 每个页面都是三节

| 节 | 内容 | 回答什么 |
| --- | --- | --- |
| 1. 项目架构 → 实际代码依赖 | **两套本体**：1.1 平台架构（**运行时组件**：浏览器 / SPA / ASGI / DRF / 数据库 / 线程 / 引擎原语 / 外部系统，10 条带协议或动作的连线 + `engines/` 边界 + 3 张结论卡）；1.2 实际代码依赖（**目录**怎么切 + 7 条边 + import/HTTP 次数，点节点高亮） | 先看系统**由什么组成、一次请求怎么走**，再看**代码切成几块、谁引用谁多少次** |
| 2. 模块依赖关系 × 模块代码量 | 左：依赖图 / import 次数表（两个 tab）；右：代码量饼图 | 谁引用谁、各占多少 |
| 3. 各模块单元代码量 | 每模块一张三系列柱状图（本次 / 最近一次 / 最近两次） | 每块代码在长还是在缩 |

第 1 节的两张图**不同源、不能互相验证**：1.1 来自 `dev_docs/ARCH_PRD/ARCH-平台架构图.spec.json`（人工语义，经 `tools/gen_arch_data.py` 转快照），1.2 来自 `tools/gen_board_data.py` 的 AST 解析。图形语言取自 `.agents/skills/arch-diagram-lite`，只用平台令牌落地，不引任何 viewer。

三个数字口径（模块 / 单元 / 依赖）每页不同，见 [`AGENTS.md`](AGENTS.md) 的「指标口径」一节——**五页数字不可横向相加**。

## 目录

| 路径 | 职责 |
| --- | --- |
| `index.html` · `overview.js` | **入口页**（总览，数据键 `projectModules`），资源引用是同级（`styles.css` / `data/` / `vendor/` …） |
| `html/` | **其余 26 个页面**（4 个分类页 + 22 模块页）；资源引用一律 `../`，指向入口写 `../index.html` |
| `html/frontend.html` · `frontend.js` | 前端页（`frontendModules`） |
| `html/frontend-<key>.html`（10）+ `html/backend-<key>.html`（12）· `module.js` | 模块页（每个业务模块一页） |
| `html/backend.html` · `backend.js` | 后端页（`backendModules`） |
| `html/agents.html` · `agents.js` | 引擎页（`engineModules`） |
| `html/ae-harness.html` · `ae-harness.js` | 原型链路页（`ae_harness`） |
| `styles.css` | 五页共用：令牌子集 + 骨架 + 组件配方 |
| `markdown.js` | AGENTS.md 弹层用的极简 markdown 渲染（共享） |
| `charts/chart-framework.js` | 图表底层：生命周期 + 令牌 + `<viz-chart>` |
| `charts/board-options.js` | 纯函数 option 构造器（`depGraph` / `modulePie` / `unitTrendColumn` …） |
| `data/board.js` · `board.json` | 代码快照（`window.__BOARD__` / 机器可读） |
| `data/architecture.js` · `architecture.json` | 平台架构快照（`window.__ARCH__`，由 `ARCH-平台架构图.spec.json` 转出） |
| `data/history.json` · `history.js` | 历史快照（生成器追加，数值没变不追加） |
| `tools/gen_board_data.py` | 生成器：扫仓库 → 写 `board.*` 与 `history.*` |
| `tools/gen_arch_data.py` | 生成器：读架构 spec → 写 `architecture.*`（校验 + 转格式，不改写语义） |
| `tools/gen_module_pages.py` | 按模板批量生成 22 个模块页到 `html/` |
| `tools/sync_sidebar.py` | 按 `data/board.json` 刷新侧栏（根入口 + 4 个分类页 + 模块页模板） |
| `tools/count_frontend.mjs` | 前端计数（本地 TypeScript 语法树，无网络） |
| `vendor/` | Vue 3.5.44 全局构建 + ECharts 5.6.0 完整构建（本地化） |

## 数据怎么来

```bash
.venv\Scripts\python.exe dev_docs/project-viz/tools/gen_board_data.py          # 代码快照（1.2 / 第 2、3 节）
.venv\Scripts\python.exe dev_docs/project-viz/tools/gen_board_data.py --check  # 比对，过期退出码 1
.venv\Scripts\python.exe dev_docs/project-viz/tools/gen_arch_data.py           # 架构快照（1.1）
.venv\Scripts\python.exe dev_docs/project-viz/tools/gen_arch_data.py --check   # 比对，过期退出码 1
```

> 必须用 `.venv` 的 Python：系统 `python` 缺 `tzdata`（`ZoneInfo("Asia/Shanghai")` 会抛错）。
> `data/*.json` 由上一次生成它的解释器持有 ACL，换解释器写会 `PermissionError` —— 详见 [`AGENTS.md`](AGENTS.md)「已知坑」。

- **1.1 平台架构是人工语义**：组件、连线、标签全部来自 `ARCH-平台架构图.spec.json`（已评审），
  `gen_arch_data.py` 只做校验 + 转格式；**页面不许改写、补全、推断**，改架构先改 spec 再重跑。
- **1.2 的依赖**来自 AST 解析的 `import`：只证明"引用了谁"，**不证明运行期谁调谁**。
- **前端 → 后端**是另一类关系：`count_frontend.mjs` 采集的 api-client 调用（图上橙色虚线、按「处」计），不是 import。
- **三层对比**靠历史累积：每次生成追加一条，页面取最近三次；历史里没有的位显示「待记录」，不补零。
- **页面不 fetch**：`file://` 下会被 CORS 拦，所以两个生成器都额外写一份 `window.__XXX__ = …` 的 `.js`。

## 已定 / 未定

**已定**：五页三节结构、每页的模块与单元口径、总览第 1 节的两套本体（1.1 平台架构 = 运行时组件 + 协议/动作连线 + 边界 + 3 张结论卡；1.2 实际代码依赖 = 目录切块 + import/HTTP 次数）、依赖图与饼图、三次对比、AGENTS.md 弹层、ae_harness 页的「外部装配方」表。

**未定**：历史趋势的更长视图（现在只到三次）、跨页跳转（点模块跳到对应页）。

## 约束（改这个目录前先看）

1. 视觉只取 [doodle-craft](../../.agents/skills/doodle-craft/SKILL.md) 的令牌，不写色值字面量。
2. 架构图（第 1 节）按 [arch-diagram-lite](../../.agents/skills/arch-diagram-lite/SKILL.md) 的语法画：分层行 / 三行节点卡 / 角色图例 / 区域边界 / 正交布线 / 边标签。**不引 archify viewer**（815 KB，多了主题/导出/雷达等本项目不要的能力）。
3. 图表必须走 `<viz-chart>`，禁止页面里直接 `echarts.init`；自绘 SVG 的架构图例外（它本来就是手绘示意图）。
4. 不引 CDN、不写网络字体；新增依赖先进 `vendor/`。
5. 数字必须能追到生成器的某段口径；解释不了的不上表。
6. 改完跑 `node --check` 六个 js + 两个生成器的 `--check` + Playwright 打开五页截图，确认零 console 错误、版式不裁剪。
