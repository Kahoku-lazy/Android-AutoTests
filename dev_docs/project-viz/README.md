# 项目可视化

把**任意一个目录**画出来：平台架构、目录依赖、代码量分布、AGENTS 文档关系。**1 个页面、4 节、双击即开、断网可用。**

一次只维护**一个层级**：`--target` 决定"模块"是谁，生成器按这个层级覆盖 `data/`，页面刷新即变；文档关系（第 4 节）是**全仓**的，不随 target 变。

## 打开

**双击 [`index.html`](index.html) 即可**（数据打包在 `data/viz.js` 与 `data/docs.js`，`file://` 下不用起服务）。

也可以走 HTTP：

```bash
python -m http.server 8811 --directory dev_docs/project-viz
# http://127.0.0.1:8811/index.html
```

## 四个视图（四个问题）

| 节 | 内容 | 数据源 | 回答什么 |
| --- | --- | --- | --- |
| 1. 平台架构 | 运行时组件 + 带协议/动作的连线 + 边界 + 结论卡 | `config/architecture.<slug>.json` | 系统由什么组成、一次请求怎么走 |
| 2. 目录依赖 | 模块节点 + import 实线 / 前端→后端 HTTP 橙虚线 | `data/dependencies.json` | 谁引用谁、谁调谁 |
| 3. 代码量分布 | 横向条形（降序）+ 占比环形 + 明细表 | `data/code-stats.csv` | 哪块最大、各占多少 |
| 4. 文档关系 | AGENTS 约束树：层级 / 管辖目录 / 引用的模块文档；点节点看全文 | `data/docs.js` | 改这块之前该读哪几篇、谁管哪里 |

## 模块是什么（`--target`）

**模块 = 目标目录展开的首层条目（目录或代码文件），只展开这一级。**

| 命令 | 模块集合 |
| --- | --- |
| `--target .`（默认） | 仓库首层有代码的条目：`frontend` / `backend` / `engines` / `tests` / `utils` / `run.py` / `run_daphne.py` / `manage.py` |
| `--target engines` | `engines` 首层（`ae_harness` 就是其中一个模块） |
| `--target engines/ae_harness` | 7 个原语模块：agents / tools / knowledge / assistant / workflow / event / middleware |
| `--target backend/apps` | 12 个 Django app |

## 更新数据（一条命令）

```bash
.venv\Scripts\python.exe dev_docs/project-viz/tools/gen_viz_data.py --target .
.venv\Scripts\python.exe dev_docs/project-viz/tools/gen_viz_data.py --target engines/ae_harness
.venv\Scripts\python.exe dev_docs/project-viz/tools/gen_viz_data.py --check      # 只比对是否过期
```

> 必须用 `.venv` 的 Python：系统 `python` 缺 `tzdata`，`ZoneInfo("Asia/Shanghai")` 会抛错。
> 生成器**一次写完三份产物**，不需要第二步内联。

## 产物

| 路径 | 内容 | 谁用 |
| --- | --- | --- |
| `data/code-stats.csv` | 模块级 `module,loc,files,units`（文件模块的 units 留空，页面显示「—」） | 第 3 节图表与明细表 |
| `data/dependencies.json` | `{target, slug, generated_at, edges}` | 第 2 节依赖图；`--check` 比对 |
| `data/viz.js` | 前两份 + 架构 JSON 合成 `window.__VIZ__` | **第 1–3 节的数据入口**（`file://` 可加载） |
| `data/docs.js` | 58 篇文档的**全文** + 层级/管辖/引用三类边 = `window.__DOCS__` | 第 4 节文档图与正文面板 |
| `config/architecture.<slug>.json` | 架构（人工语义，代码检测不出来，由 Agent 维护） | 第 1 节架构图 |

`slug` 由 target 派生：`.` → `repo-root`，`engines/ae_harness` → `engines-ae-harness`。

> `docs.js` 约 200KB（全部 markdown 内联）。这是**故意**的：`file://` 下不能 `fetch`，不内联就没法在页面里读原文。它不随 `--target` 变。

## 文档关系（第 4 节）

- **节点**：所有 `AGENTS.md`（含 `.agents/AGENTS.md` 与 `dev_docs/project-viz/AGENTS.md`）+ `.agents/docs/**/*.md`，共 58 篇。
- **三类边**：
  - 实线 **层级**：父 AGENTS.md → 子 AGENTS.md（按目录就近取父级）；
  - 虚线 **管辖**：AGENTS.md → 它所在目录（根文档管整仓）；
  - 实线 **引用**：AGENTS.md 里 markdown 链接指向的模块文档。
- **点任意节点**：右侧显示标题、路径、大小、管辖目录、出链/入链，再接**全文**（等宽，可滚动）。
- 管辖目录按**文档所在位置**取，不解析正文里的反引号路径——那些既可能是仓库相对也可能是文档相对，还混着 `<模块>` / `{app}` 占位符，解出来只会把图撑满噪声节点。

## 架构 JSON（手写，每层级一份）

```jsonc
{
  "title": "…",
  "components": [
    { "id": "api", "type": "backend", "label": "Django + DRF",
      "sublabel": "12 个 App · /api", "tag": "backend/", "row": 0, "col": 3 }
  ],
  "connections": [ { "from": "spa", "to": "asgi", "label": "axios · /api", "variant": "default" } ],
  "boundaries":  [ { "label": "engines/ · 零 django 依赖", "wraps": ["support", "harness", "bridge"], "pad": 22 } ],
  "cards":       [ { "title": "三层分工", "items": ["…"] } ]
}
```

- 坐标只写 `row` / `col`（0 起）；页面用固定间距排版，`row/col` 缺省时按顺序自动铺。
- `type` 取 `frontend` / `backend` / `database` / `security` / `external`，决定节点色条与图例。
- 该层级没有配置文件时，第 1 节显示空态并提示要写的文件路径——**不编造架构**。

## 文件

| 路径 | 职责 |
| --- | --- |
| [`index.html`](index.html) | 唯一页面（内联 CSS + JS，无构建） |
| `tools/gen_viz_data.py` | 生成器：扫目标目录 + 全仓文档 → 写 4 份产物 |
| `tools/count_frontend.mjs` | 前端计数（供生成器判断前后端并存时的 HTTP 边） |
| `config/` | 每层级一份手写架构 JSON |
| `data/` | 生成器的输出（4 份），页面只读 |
| `vendor/echarts.min.js` | 本地 ECharts，只给第 3 节两张图用 |

规则、口径与踩坑记录见 [`AGENTS.md`](AGENTS.md)。

## 边界

- **目录级视图只画代码**：`.md` / `.json` / `.csv` 不算代码行，`data/` 与 `vendor/` 不进模块。所以像本目录这种"文档级目录"，第 2、3 节只会出现 `tools/` 与 `index.html` 两个模块——这是**有意的边界**，不是漏算。
- **一次一个层级**：`--target` 覆盖同一份 `data/`，不保留多层级快照（文档图例外：它始终是全仓）。
- **依赖只证明"引用了谁"**：不证明运行期调用顺序。
- **架构是人工语义**：来自 `config/`，不是 AST 解析，也不与依赖数字互相验证。
- **文档图不判断"该不该读"**：它只画仓库里写明的层级与链接关系；哪些是红线、哪些过时，还得看原文。
- **旧版 27 页看板**已归档到 `temps/project-viz_view/`；旧 spec（`dev_docs/ARCH_PRD/ARCH-平台架构图.spec.json`）与 `gen_arch_data.py` 已废弃，架构以 `config/` 为准。
