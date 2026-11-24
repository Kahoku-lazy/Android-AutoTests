## Context

触点只有三处，约束如下：

1. **旧链路是两段式且写死层级**：`tools/gen_board_data.py`（2,339 行）扫仓库写 6 份产物，`gen_data.py` 再挑 15 行内联成根目录 `data.js`；页面只读 `window.MINI`。想画 `engines/ae_harness` 只能改代码。
2. **产物大多无人读**：`data/` 672.6KB 中约 92% 是 `board.json`≡`board.js`、`history.json`≡`history.js` 的双份序列化。
3. **`file://` 是硬约束**（红线 5）：双击必须能开，数据只能以 `<script src>` 外壳加载，不能用 `fetch`。

需求方决策：架构图与依赖图用 JSON、代码量用 CSV、生成器同时写 `.json` 与 `.js` 外壳；`--target` 选层级（一次一个、覆盖产物）；架构**每层级一份手写 JSON**，放新建的 `config/` 目录，旧 spec 与 `gen_arch_data.py` 废弃。

## Goals / Non-Goals

**Goals:**

- 三份产物 + 一份加载壳，每份都有明确消费者；生成器只保留一套通用采集逻辑。
- `--target` 让同一套代码画出任意层级（仓库根 / engines / engines/ae_harness / backend/apps …）。
- 页面版式冻结，但节点位置数据驱动（否则任意层级都会丢节点）。
- 更新从两步变一步；`--check` 能发现过期。

**Non-Goals:**

- 不修 6 个非令牌色值（红线 3 历史遗留，属视觉变更另案）。
- 不做多层级快照并存（页面不切换层级，只反映最后一次生成）。
- 不为本目录新增自动化测试或接入 CI。
- 不恢复历史趋势图、不做节点拖拽、不改 `.gitignore` 例外。

## Decisions

### D1 一份加载壳 `data/viz.js`，不逐份配 `.js`

页面要一次性拿到三节数据。三个 `<script src>` 意味着三个加载点、三处失败可能、三个全局名；一个 `window.__VIZ__` 只多 4KB。

**备选**：① 每份 `.json` 各配 `.js`（更自解释，但 6 个文件、3 个全局）；② 直接 `fetch` JSON（必须起 http 服务，破红线 5）。选 D1。

### D2 产物分工：CSV 存数字、JSON 存边与元信息、viz.js 只是外壳

| 产物 | 内容 | 消费者 |
| --- | --- | --- |
| `data/code-stats.csv` | `module,loc,files,units`（N 行，文件模块 units 空） | 第 3 节；`--check` |
| `data/dependencies.json` | `{target, slug, generated_at, edges}` | 第 2 节；`--check` |
| `data/docs.js` | 58 篇文档全文 + 三类关系 = `window.__DOCS__` | 第 4 节；`--check` |
| `config/architecture.<slug>.json` | 架构（组件/连线/边界/结论卡） | 第 1 节；`--check` 间接（经 viz.js） |
| `data/viz.js` | CSV + deps + 架构合成 `window.__VIZ__` | 第 1–3 节唯一入口 |

模块清单**只存在 CSV 里**，`dependencies.json` 不重复序列化模块——旧版「同一份数据两种写法」正是要删的复杂度。
**备选**：保留旧长表（`snapshot_rank,scope,module,unit,metric,value`，1,008 行）以便将来下钻 —— 那是「为未消费的将来保留数据」，明确放弃。

### D3 `--target` 决定模块：首层、含文件、单层级覆盖

- 模块 = 目标目录的直接子项（目录或代码文件），**只展开一级**；不含代码的目录不算模块。
- 目录模块的 `loc/files` 递归汇总其代码文件（排除 `migrations/`、`__init__.py` 等），`units` = 直接子项数；文件模块 `units = None`。
- `slug` 由 target 派生（`.`→`repo-root`，`engines/ae_harness`→`engines-ae-harness`），同时决定架构配置文件名与页面脚注。
- 覆盖写：一次只维护一个层级，避免「多层级快照并存」的产物爆炸。

### D4 依赖解析用「点分名 → 模块」索引，而不是只看 import 头

旧实现只取 `import` 的头段（`head in known`），在 `engines/ae_harness` 这种层级下会全部落空（模块是 `agents`/`tools`…，而 import 头是 `engines`）。改为：为每个 `.py` 生成点分名与包名索引，绝对导入按全名匹配、相对导入按 `level` 回退包路径。代价是 `dotted_owner` 多登记一遍包名，收益是任意层级都能算对。

**备选**：只用 `__init__.py` 建包表 —— 但 `__init__.py` 不计入代码文件，包名就丢了；所以显式登记「文件所在包名」。

### D5 节点位置数据驱动，样式冻结

- 架构图：`components` 带 `row`/`col`（0 起），页面按固定间距 `320×200`、卡面 `224×88` 排版；缺 `row/col` 时按顺序自动铺。连线按节点边框裁切，横/竖/斜共用一套 `anchor()`，旧版「只两种走法」在任意图上仍然成立（同行必横、同列必竖）。
- 依赖图：按模块数自动铺网格（`cols = min(4, ceil(sqrt(n)))`），边同样用 `anchor()` 裁切；配色按模块顺序取 6 色调色板，仓库根五块的配色与旧版一致。
- **理由**：版式（卡片/配色/粗边/微倾/右对齐）是需求方要冻结的部分；坐标若写死，`--target` 一换就有节点被静默丢掉。

### D6 架构 `config/` 每层级一份，旧 spec 废弃

架构是人工语义、代码检测不出来，只能由 Agent 写。`config/architecture.<slug>.json` 成为唯一真相源；`gen_arch_data.py`（153 行）与 `ARCH-平台架构图.spec.json` 退出管线。缺配置时第 1 节显示空态并提示路径，**不编造**（红线 1）。

### D7 口径修正：剔除 `migrations/` 与 `__init__.py`

旧实现没排除这两类，与本目录自己声明的口径相反。新实现按口径排除，因此 backend 约 −5.3k 行（155 个 migration 文件）、engines 约 −740 行（26 个 `__init__.py`）。这是**修正而非漂移**，已在 README/AGENTS 注明，避免下次有人以为是 bug。

**目录级视图只画代码（2026-11-24 需求方确认）**：`.md` / `.json` / `.csv` / `.yaml` 不计入代码行，`data/`、`vendor/` 不进模块。后果是文档级目录（如 `dev_docs/project-viz` 自己）的第 2、3 节只有 `tools/` 与 `index.html` 两个模块——这是有意的边界，**不为了让图好看而放宽口径**。

### D9 文档关系：三类边 + 全文内联 + 泳道布局

- **节点**：全仓 `AGENTS.md`（含 `.agents/AGENTS.md`、`dev_docs/project-viz/AGENTS.md`）+ `.agents/docs/**/*.md`，共 58 篇；另加每个 AGENTS 的管辖目录（8 个）。
- **三类边**：层级（父 AGENTS → 子 AGENTS，按目录就近取父级）、管辖（AGENTS → 所在目录）、引用（AGENTS 里 markdown 链接指向且存在的模块文档）。
- **全文内联**：`file://` 不能 `fetch`，所以正文直接进 `data/docs.js`（约 200 KB）。这是需求方明确选择的代价：**能读原文 > 体积小**。
- **泳道布局**：一个 AGENTS 一条泳道（横排），其引用的模块文档顺泳道竖排——57 个文档节点若按深度分层会横向铺到几千像素、字看不清。
- **管辖目录按位置取，不解析正文反引号**：正文里的路径混着仓库相对 / 文档相对 / `<模块>` 占位符，解析只会产生几十个噪声节点（实测 53→8）。
- **与 `--target` 解耦**：文档是全仓事实，切层级不重扫文档；页面脚注只标 1–3 节的 target。

## 模块防火墙自检

本变更不涉及 Django app、数据库、平台前后端代码，逐条确认：

- **跨 App import**：不适用 —— 本目录不 import 任何 `backend/apps/**`。
- **禁止跨 App import service/runner/consumer**：不适用。
- **INSERT/UPDATE/DELETE 收敛到 `api.py`**：不适用 —— 无数据库写入；生成器只读仓库文件。
- **前端不直连数据库；仪表盘不做写操作**：不适用 —— 页面是静态快照，零接口、零写操作。
- **反向依赖**：不适用 —— 本目录不 import `frontend/` / `backend/` / `engines/`，也不被它们引用（红线 4 维持）。

## Risks / Trade-offs

- **[数字与旧快照不一致] 容易被当成 bug** → 差异拆成两部分写进 README/AGENTS：口径修正（migrations/`__init__.py`）+ 仓库被并行会话改动；`--check` 只保证「本次生成与盘上产物一致」，不保证与历史快照一致。
- **[删除不可逆] `board.json` / `history.json` 里的历史数据** → 都是 git 跟踪文件，`git checkout -- dev_docs/project-viz` 即回滚；历史 41 条快照在 git 历史里仍可取回。
- **[单层级覆盖] 切走后再看总览要重跑** → 页面脚注显示当前 target；README 首屏写明「一次一个层级」。
- **[架构每层级手写] 子层级第 1 节容易空** → 属设计选择（宁可空态也不编造）；新增架构时只需在 `config/` 加一个文件。
- **[无测试] 重构无回归网** → 以 `--check` + `node --check`（data/viz.js 与抽取出的内联脚本）+ 打开页面核对三节替代。
- **[并发会话] 仓库正在被改动** → 本次只写 `dev_docs/project-viz/` 与 openspec 规划产物；数字是「扫描那一刻」的快照。

## Migration Plan

已执行（本变更落地顺序）：

1. 备份旧 `project` 模块级数字到 `temps/viz-baseline-project.json`。
2. 新建 `config/architecture.repo-root.json`（旧 `data/architecture.json` 迁移 + 补 `row/col`）。
3. 新建 `tools/gen_viz_data.py`，先跑通 `--check` 与三档 target（`.` / `engines/ae_harness` / `backend/apps`）。
4. 改 `index.html`：`window.__VIZ__`、数据驱动排版、空态、页脚 target、修正错误命令文案。
5. 删除 `tools/gen_board_data.py`、`tools/gen_arch_data.py`、`gen_data.py`、`data/` 下 7 个旧产物、根 `data.js`。
6. 重写 `README.md` 与 `AGENTS.md`。
7. 验证：`--check` 退出 0、`node --check` 两份 JS、抽取内联脚本语法通过。
8. **回滚**：`git checkout -- dev_docs/project-viz`（改动全在本目录内，无外部契约）。
