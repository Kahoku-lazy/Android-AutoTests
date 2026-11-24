# project-viz AGENTS.md

> 层级：根 [`AGENTS.md`](../../AGENTS.md) → **本文件**。本文件只约束 `dev_docs/project-viz/`，不改平台代码；与上级冲突时以上级为准。

## 一句话

**把任意一个目录画出来**：1 个页面（平台架构 / 目录依赖 / 代码量分布 / AGENTS 文档关系）+ 一个按 `--target` 采样的生成器。文档级产物，不进 Vite 构建、不接后端接口、不参与 CI 门禁。

## 数据怎么流（唯一的链路）

```
config/architecture.<slug>.json ──（人工语义，Agent 手写，不改不生成）
                                          │
tools/gen_viz_data.py --target <目录> ──► data/code-stats.csv     （模块级指标）
                                       ├─► data/dependencies.json （依赖边 + 快照时间）
                                       ├─► data/viz.js            （1–3 节合成 window.__VIZ__）
                                       └─► data/docs.js           （全仓文档全文 + 关系 = window.__DOCS__）
                                                                        │
                                                                index.html（唯一页面，4 节）
```

**一次生成 = 四份产物**（`--target` 覆盖前三份，文档那份始终是全仓）。页面**不扫描仓库、不 fetch**。

## 目录职责

| 路径 | 职责 | 谁改 |
| --- | --- | --- |
| [`index.html`](index.html) | **唯一页面**：样式 + 四节渲染脚本（内联 JS，无构建） | 改视图时 |
| `tools/gen_viz_data.py` | 生成器：扫目标目录 + 全仓文档 → 写 4 份产物；`--check` 只比对 | 改口径 / 加层级时 |
| `tools/count_frontend.mjs` | 前端计数（Node + TS，供生成器判断前后端并存时补 HTTP 边） | 只在前端计数口径变化时改 |
| `config/architecture.<slug>.json` | 每层级一份**手写**架构（组件/连线/边界/结论卡） | Agent 手写，生成器只读 |
| `data/code-stats.csv` | 模块级指标表（第 3 节唯一数字源） | **只由生成器写** |
| `data/dependencies.json` | 依赖边 + `generated_at` + `slug` | **只由生成器写** |
| `data/viz.js` | 上面两份 + 架构合成 `window.__VIZ__`（`file://` 可加载） | **只由生成器写** |
| `data/docs.js` | 58 篇文档的全文 + 层级/管辖/引用三类边 = `window.__DOCS__`（约 200KB，故意的） | **只由生成器写** |
| `vendor/echarts.min.js` | 本地 ECharts 5.6.0，**只给第 3 节两张图用** | 只有升级 ECharts 时替换 |

> `data/` 里**只允许**这四份产物。不要新增「同一份数据的第二种序列化」——旧版的 `board.json`≡`board.js`、`history.json`≡`history.js` 就是为此删掉的。

## 页面结构（固定四节）

| 节 | 内容 | 数据源 | 图型 |
| --- | --- | --- | --- |
| 1. 平台架构 | 组件节点 + 带协议/动作的连线 + 边界虚框 + 结论卡 | `config/architecture.<slug>.json` | 手写 SVG，位置来自 `row/col` |
| 2. 目录依赖 | 模块节点 + import 实线 / HTTP 橙虚线 | `data/dependencies.json`（节点来自 CSV） | 手写 SVG，网格布局 |
| 3. 代码量分布 | 横向条形（降序）+ 占比环形 + 明细表 | `data/code-stats.csv` | ECharts（bar / pie） |
| 4. 文档关系 | AGENTS 约束树（层级 / 管辖 / 引用）+ 右侧面板看全文 | `data/docs.js` | 手写 SVG，分泳道 |

**四节 = 四个问题**：由什么组成、谁引用谁、哪块最大、改之前该读哪几篇。加视图前先回答"补的是哪个问题"。

## 模块与口径

**模块 = `--target` 目录的展开首层（目录或代码文件），只展开这一级。**

- `--target .`（默认）：仓库首层有代码的条目（`backend` / `engines` / `frontend` / `tests` / `utils` / `run.py` / `run_daphne.py` / `manage.py`）。
- `--target engines/ae_harness`：7 个原语模块。
- **代码行** = 非空物理行（`.vue` 含 template/style）；**文件** = 代码文件数（排除 `__init__.py`、`__pycache__`、`migrations/`、`vendor/`、`logs/`、`temps/`、`data/`、`dev_docs/`、`node_modules/`）。
- **单元** = 目录模块的直接子项数（子目录需含代码才算）；模块本身是文件时为 `None`，页面显示「—」。
- **依赖** = 一个文件对同一目标模块只计一次；`import` 标"条"，前端→后端的 **HTTP 调用**标"处"，只有模块集合同时含 `frontend` 与 `backend` 时才补这条边。
- **只画代码**：模块必须是代码文件（`.py/.ts/.tsx/.vue/.js/.mjs/.css/.html`）或含代码文件的目录。`.md` / `.json` / `.csv` / `.yaml` **不算**代码行，`data/`、`vendor/` 等排除。所以 `--target dev_docs/project-viz` 只会得到 `tools/` 与 `index.html` 两个模块——这是**有意的边界**（2026-11-24 需求方确认），不要为了"让图好看"把文档或配置算成代码。
- `slug` = target 路径转小写连字符（`.` → `repo-root`，`engines/ae_harness` → `engines-ae-harness`），同时决定架构配置文件与页面显示。

## 红线（违反即返工）

1. **不得冒充结论**：没有真实数据前，不画假图表、不填假数字、"待定"就写"待定"。该层级缺架构配置时显示空态，不许编。
2. **不得预设方案**：新增视图前，先在 README 写清目标（给谁看、回答什么问题）与指标口径；没有目标和口径就不加视图。
3. **视觉不自创**：纸面 `#f3efe2` / 卡片 `#f7f3e8` / 墨色 `#1e1e24` / 粗边 2px / 硬影 0 模糊 / 微倾，取自 [doodle-craft](../../.agents/skills/doodle-craft/SKILL.md) 与 [`tokens.css`](../../frontend/src/shared/styles/tokens.css)；**页面里只允许出现令牌的复制值，不许写别的色**。
4. **不污染平台**：不 import `frontend/`、`backend/`、`engines/` 的代码，不调生产接口，不把本目录塞进任何构建链。
5. **断网可开**：页面不得依赖 CDN / 网络字体 / 远程脚本；新增依赖必须本地化进 `vendor/`。**`file://` 双击必须能开**——数据靠 `data/viz.js`、`data/docs.js` 这两个 `<script src>` 外壳加载，**不许改用 `fetch` 读 JSON / CSV / Markdown**。
6. **数据只读**：一律只读仓库；**禁止**把密钥、`.env`、数据库内容、用户数据写进 `data/` 或页面里。
7. **图表只用本地库 + 手写 SVG**：ECharts 只能来自 `vendor/echarts.min.js`（禁止 CDN）；**结构图（架构 / 依赖）用手写 SVG，不塞进 ECharts**。

## 改这个目录的顺序（别跳）

1. **定目标**：哪个问题没被回答？
2. **定口径**：数字数什么、从哪取。需要新指标 → 改生成器，**不改页面**。
3. **跑生成**：`gen_viz_data.py --target <目录>`。
4. **改页面**：只动 `index.html` 的渲染脚本与样式；版式冻结，变量随数据。
5. **写架构**（该层级要有架构图时）：在 `config/` 新建 `architecture.<slug>.json`，再重跑一次生成。
6. **自检**：见下节。

## 已知坑

### 数据 / 生成器

- **必须用 `.venv` 的 Python**：系统 `python` 缺 `tzdata`，`ZoneInfo("Asia/Shanghai")` 直接抛 `ZoneInfoNotFoundError`。
- **一次一个层级**：`--target` 会**覆盖** `data/`；看完子层级要切回总览，得再跑一次 `--target .`。页面脚注会显示当前视图，别拿子层级数字当全仓。
- **快照会过期**：代码一改，数字就旧了。提交前跑 `--check`（有差异退出码 1）。
- **生成前确认没有人在改仓库**：并行会话会让两次生成之间总行数变化，`--check` 反复报"已过期"。
- **口径与旧版有两处差异**（数字会变小，不是 bug）：旧实现没排除 `migrations/`（backend 约 5.3k 行）与 `__init__.py`（engines 约 740 行），与本文件声明的口径不一致；现在的实现按口径排除。
- **`data/*.json` 偶尔被上一次生成它的解释器"锁住"**：换解释器写会 `PermissionError`（ACL 里 `S-1-4-…` 是 AppContainer 令牌）。解法：先用要用的解释器把旧文件读出来重建成新文件，再跑生成器。
- **别把 `--check` 做成"永远过期"**：比对必须忽略 `generated_at` / `generatedAt`（生成器已这么做，改比对逻辑时别退回去）。
- **文档那份产物不随 `--target` 变**：`docs.js` 每次生成都重扫全仓文档；切层级只影响 1–3 节的数据。
- **`docs.js` 约 200KB 是故意的**：`file://` 不能 `fetch`，不内联全文就没法在页面里读原文。别为了"体积好看"改成只留摘要。
- **管辖目录按位置取，不解析正文**：`.agents/docs/**` 里那些反引号路径混着仓库相对 / 文档相对 / `<模块>` 占位符，解析出来会把图撑成几十个噪声节点。要看某篇文档"写了哪些路径"，去右侧面板读原文。
- **`.agents/AGENTS.md` 是 0 字节**：它会作为「空文件」节点出现，是真实状态，不要为了让图好看而过滤掉。

### 口径 / 语义

- **数字要能解释**：页面每个数都能追到生成器某段口径；解释不了的不上表。
- **两套本体不同源**：第 1 节架构来自手写 `config/`（**人工语义**），第 2 节依赖来自 AST 静态解析。**不能互相验证**，也不要拿一个去"修"另一个。
- **依赖只证明"引用了谁"**：不证明运行期谁调谁，页面文案已写明，别在别处说成调用链。
- **前端 → 后端是 HTTP 调用，不是 import**：`kind: "http"`，图上橙色虚线、"处"作量词；图例必须写清，否则会被当成 import。
- **改架构只改 `config/`**：不要在 `index.html` 里加节点、改连线、换标签；页面只负责排版与着色。

### 页面 / 渲染

- **目录名带连字符，`python -m` 用不了**：直接 `python dev_docs/project-viz/tools/gen_viz_data.py` 运行。
- **节点位置来自数据**：架构图用 `row/col`，依赖图按模块顺序自动铺网格；**不要再写死坐标常量**（旧版 `APOS`/`DPOS` 已删）。
- **表头也要右对齐**：`.num` 必须同时作用于 `th` 和 `td`，只写 `td.num` 会让表头左对齐、数字右对齐，视觉上整列错位（踩过）。配套：`table-layout:fixed` + `<colgroup>` 固定列宽。
- **ECharts 在 `file://` 下可用**：因为它是 `<script src>` 本地加载，不走 `fetch`；但 `init` 前容器必须有高度，否则算出 0×0。
- **改这个目录的 JS / HTML 禁止用 PowerShell 的 `Get-Content -Raw` + `Set-Content`**：它按 GBK 解码 UTF-8 再写回，中文会变乱码且不可逆。用 `edit` / `write`，或 Python 显式 `encoding="utf-8"`。
- **`.gitignore` 只有一条例外**：`!dev_docs/project-viz/index.html`（`dev_docs/**/*.html` 会吃掉其余 html）。新增页面要同步加例外，并用 `git check-ignore -v <路径>` 验证。

## 自检（改完跑一遍）

```bash
# 1. 语法（index.html 的内联脚本先抽出来）
node --check dev_docs/project-viz/data/viz.js
node --check dev_docs/project-viz/data/docs.js
python -c "import pathlib,re;h=pathlib.Path('dev_docs/project-viz/index.html').read_text(encoding='utf-8');pathlib.Path('temps/viz-inline.js').write_text('\n'.join(re.findall(r'<script>(.*?)</script>',h,re.S)),encoding='utf-8')"
node --check temps/viz-inline.js

# 2. 数据与代码一致
.venv\Scripts\python.exe dev_docs/project-viz/tools/gen_viz_data.py --check

# 3. 打开验证（双击即可，或起服务）
python -m http.server 8811 --directory dev_docs/project-viz
# http://127.0.0.1:8811/index.html
```

```
[ ] 页面零 console / pageerror（`file://` 与 HTTP 各开一次）
[ ] 四节都在：架构 11 节点 / 10 连线；依赖节点数 = 模块数、边数 = JSON 里的边数；条形行数 = 表格行数；文档图节点数 ≥ 文档数
[ ] 表格：表头与数字右对齐（getBoundingClientRect 差值 < 1px）；文件型模块的「单元」为「—」
[ ] 色值只出现令牌复制值；阴影无模糊；卡片有微倾
[ ] 数字与 data/ 的 CSV 一致；合计 = 各行之和
[ ] 页脚显示的 target 与本次 `--target` 一致
[ ] 点第 4 节任意节点，右侧出现该文档全文（`<pre>` 里能看到正文）；点管辖节点能列出管辖它的文档
[ ] README 的口径表与页面文案一致
```
