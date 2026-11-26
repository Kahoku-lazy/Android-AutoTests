# 看板模板怎么用

复制这 4 个文件到目标仓库的看板目录，改下面 5 处，就能出一版可用的看板。

```
<看板目录>/
├── gen_data.py                  ← 从 gen_data.template.py 复制
├── <name>.html                  ← 从 page.template.html 复制
├── <name>.js                    ← 从 app.template.js 复制
└── data/                        ← 生成器产出，不用手建
```

页面依赖同目录的 `styles.css`、`vendor/`（Vue + ECharts）、`charts/`（图表底层）。**这些是必须提前就位的共享资产**，模板只提供结构与逻辑。

## 要改的 5 处

| # | 文件 | 改什么 |
|---|---|---|
| 1 | `gen_data.py` | `MODULE_ROOT`（模块所在目录）、`MODULES`（模块 key + 中文名，顺序即页面顺序）、`SKIP_DIRS` / `SKIP_FILES` |
| 2 | `gen_data.py` | `_relations()` 里识别模块的那段：按目标仓库的包路径前缀改（模板里认的是 `apps.<key>`） |
| 3 | `<name>.js` | `MODULE_COLOR_KEY`：模块 → 令牌色名（`tokens().colors` 的键；不够用就在 `charts/chart-framework.js` 里加） |
| 4 | `<name>.js` | `DIAGRAM_LAYOUT` / `DIAGRAM_EDGES`：架构图的节点坐标与边。**边必须能对回数据**，别凭语义补 |
| 5 | `<name>.html` | `__TITLE__` / `__SUBTITLE__` / `__DATA_JS__` / `__APP_JS__` 四个占位符，以及侧栏导航 |

## 跑起来

```bash
python <看板目录>/gen_data.py            # 写 data/board.json + board.js + history.*
python <看板目录>/gen_data.py --check    # 提交前比对，过期退出码 1
python -m http.server 8899 --directory <看板目录>   # 必须用 HTTP 打开
```

## 三节各放什么

| 节 | 内容 | 数据来源 |
|---|---|---|
| 1 | 模块关系图（SVG，点节点高亮相关线） | `DIAGRAM_EDGES`（人工坐标）+ 数据的 `relations` |
| 2 | 左：依赖图 / import 表 tab；右：每模块一张卡片 | `relations` + `modules[].totals` |
| 3 | 每模块一张三系列柱（本次/最近一次/最近两次）+ 三张总量卡 | `modules[].units[].trend` + `modules[].totalTrend` |

## 别踩的坑

完整 20 条见 [`../references/pitfalls.md`](../references/pitfalls.md)。最常犯的：

- 页面里 `fetch('data/board.json')` → `file://` 被 CORS 拦，必须用 `board.js`
- 三个兄弟块都写 `v-else` → Vue `compiler-30` 整页白屏，用容器包起来
- `:viewBox` 动态绑定 → 被小写成 `viewbox`，写静态属性
- 数字用 SVG `<text>` 画 → 与文本基线对不齐，用 HTML 文本 + `background-clip: text`
- 改完样式用 `file://` 验证 → CSS 缓存骗你，一律 HTTP

## 模板没有的东西

- **AGENTS.md 弹层**：需要时把 `markdown.js` 一起带上，生成器读 md 进快照，节点上加 `AGENTS` 入口（实现方式见生成产物里的 `ae-harness.js`）
- **历史趋势折线**：模板只保留"最近三次对比"，更长的趋势图需要额外 option 函数
- **业务域对照表**：领域/覆盖率这类需要人工判断的映射，模板不提供，属于目标仓库自己的口径
