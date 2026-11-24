## Why

2026-11-24 的复杂度体检结论：`dev_docs/project-viz` 的复杂度**配比失衡**——页面只有 279 行，生成器却有 2,339 行 / 66 个函数 / 最大圈复杂度 63（页面的 8.4 倍）；`data/` 672.6KB 里约 92% 是**无人读取的双份序列化**（`board.json`≡`board.js`、`history.json`≡`history.js`）；5 套指标口径里页面只展示 1 套（`code-stats.csv` 1,008 行，页面只读 15 行）。

根因是历史包袱 + 口径写死：旧 27 页看板退役后它的整条数据链仍留在生成器里（**481 行函数体只喂 `board.json`**），而「画哪一层」被写死成仓库一级目录，想看 `engines/ae_harness` 或 `backend/apps` 只能改代码。同时自检已红（`--check` 报过期），本目录无测试引用、不在 CI。

## What Changes

**数据链路收敛，并把「画哪一层」变成参数：**

- 生成器 `tools/gen_viz_data.py`（替换 `tools/gen_board_data.py`）只做三件事：扫目标目录、算依赖、写产物。新增 `--target <目录>`：
  - **模块 = 目标目录的展开首层（目录或代码文件），只展开这一级**。
  - 默认 `--target .`（仓库首层）；`--target engines/ae_harness` → 7 个原语模块；`--target backend/apps` → 12 个 app。
- 架构图**改为手写 JSON**（代码检测不出来，由 Agent 维护），落在**新建的 `config/` 目录**，**每层级一份** `architecture.<slug>.json`；`tools/gen_arch_data.py` 与 `dev_docs/ARCH_PRD/ARCH-平台架构图.spec.json` **废弃**，`config/` 为唯一真相源。
- 产物收敛为「3 份真相文件 + 1 份加载壳」，全部覆盖写（**一次只维护一个层级**）：
  - `data/code-stats.csv` — 模块级 `module,loc,files,units`（第 3 节唯一数字源，文件模块 units 留空）；
  - `data/dependencies.json` — `{target, slug, generated_at, edges}`；
  - `data/viz.js` — 前两份 + 架构合成 `window.__VIZ__`，`<script src>` 加载，`file://` 双击即开；
  - `data/docs.js` — 全仓 **58 篇** AGENTS / 模块文档的**全文** + 层级/管辖/引用三类关系 = `window.__DOCS__`（约 200 KB，只在第 4 节用）；
  - `config/architecture.<slug>.json` — 手写架构（页面第 1 节唯一来源）。
- 新增**第 4 节「文档关系」**：把 `AGENTS.md` 的约束树画出来——实线层级（父文档 → 子文档）、虚线管辖（文档 → 它所在目录）、实线引用（索引 → 它列出的模块文档，共 48 条）；点任意节点在右侧看**原文全文**，断网可读。文档关系是**全仓**的，不随 `--target` 变。
- **BREAKING**（仅本目录内部契约，不涉平台代码）：
  - 根目录 `data.js`（`window.MINI`）→ `data/viz.js`（`window.__VIZ__`）；
  - `data/code-relations.csv` → `data/dependencies.json`；`data/code-stats.csv` 由 1,008 行长表改为模块级 N 行；
  - 删除 `data/board.*`、`data/history.*`、`data/architecture.*`、`gen_data.py`（两步更新变一步）。
- 页面 `index.html` **版式冻结**（四节：架构 / 依赖 / 代码量 / 文档，后三节与截图一致），但**节点位置改为数据驱动**：架构图按 JSON 的 `row/col` 排版，依赖图按模块数自动铺网格，文档图按泳道铺——否则任意层级都会有节点被静默丢掉。
- **口径修正（数字会变小，不是 bug）**：旧实现没排除 `migrations/` 与 `__init__.py`，与本目录自己声明的口径不一致；新实现按口径排除。
- 同步重写 `README.md` 与 `AGENTS.md`（数据流、目录职责、口径、更新步骤、已知坑、自检清单）。红线 1–7 **语义不变**，只有红线 5 的实现方式由「两步内联」改为「生成器直出 `viz.js`」。

## 关联文档

无 PRD 关联：本变更是文档级工具链 / 产物契约变更，不触及平台功能与接口。
依据：2026-11-24 复杂度体检 + 需求方决策（架构与依赖用 JSON、代码量用 CSV、JSON+JS 外壳供 `<script src>` 加载、单层级覆盖、每层级一份手写架构、旧 spec 废弃）。

## Capabilities

### New Capabilities

- `project-viz`: 仓库自绘看板的行为契约——三节各回答什么问题、`--target` 如何决定模块、每节数据源与口径、离线可开、一次生成、以及「每个产物必须有消费者」的复杂度护栏。

### Modified Capabilities

（无。本变更不改变任何已有平台能力的 REQUIREMENT。）

## Impact

- **仅限 `dev_docs/project-viz/`**（+ `openspec/changes/**` 规划产物）：`index.html`、`tools/gen_viz_data.py`（新增）、`tools/gen_board_data.py`、`tools/gen_arch_data.py`、`gen_data.py`（三者删除）、`data/*`（重生成）、`config/*`（新增）、`README.md`、`AGENTS.md`。
- **不动平台代码**：不 import `frontend/` / `backend/` / `engines/`，不进 Vite 构建，不接后端接口，不参与 CI 门禁。
- **不改红线语义**：`file://` 双击、断网、ECharts 只用 `vendor/`、结构图手写 SVG、数据只读、无消费者产物不留，全部维持。
- **测试**：本目录仍无自动化用例（维持现状）；自检靠 `--check` + `node --check` + 打开页面目视三节。
- **非目标**：不修 6 个非令牌色值（红线 3 历史遗留，属视觉变更另案）、不做多层级快照并存、不恢复历史趋势图、不改 `.gitignore` 例外。
