## Purpose

把仓库里任意一个目录画成一张可离线打开的静态页面：平台架构、目录依赖、代码量分布三节。本能力定义三节各自回答什么、每节的数据源与口径、`--target` 如何决定"模块"、离线与更新的硬约束，以及「每个产物必须有消费者」的复杂度护栏。

## ADDED Requirements

### Requirement: 四节内容与数据源固定

页面 SHALL 只包含四节，每节的内容与数据源 MUST 按下表固定：

| 节 | 回答的问题 | 数据源 | 图型 |
| --- | --- | --- | --- |
| 1. 平台架构 | 系统由什么组成、一次请求怎么走 | `config/architecture.<slug>.json` | 手写 SVG |
| 2. 目录依赖 | 谁引用谁、谁调谁 | `data/dependencies.json`（节点来自 `data/code-stats.csv`） | 手写 SVG |
| 3. 代码量分布 | 哪块最大、各占多少 | `data/code-stats.csv` | ECharts 条形 + 环形 + 明细表 |
| 4. 文档关系 | 改这块之前该读哪几篇、谁管哪里 | `data/docs.js` | 手写 SVG + 正文面板 |

新增视图前 MUST 先在本能力里补一条「它回答哪个问题」；回答不出问题的视图不得加入。

#### Scenario: 四节全量呈现

- **WHEN** 用浏览器打开 `dev_docs/project-viz/index.html`
- **THEN** 页面依次出现四节：架构图（节点数 = 架构 JSON 的 `components` 数、连线数 = `connections` 数）、依赖图（节点数 = 模块数、边数 = `dependencies.json` 的 `edges` 数）、代码量区（条形行数 = 环形分片数 = 明细表行数 = 模块数）、文档图（节点数 = 文档数 + 管辖目录数）

#### Scenario: 数据源缺失时不冒充结论

- **WHEN** 某一节的数据源缺失或为空
- **THEN** 该节 MUST 渲染为空态并提示缺失的文件路径，MUST NOT 填充示例数字或假图表

### Requirement: 模块由 target 决定

模块 MUST 是 `--target` 目录的展开首层条目（目录或代码文件），MUST 只展开这一级，MUST NOT 递归或跨层混算。未指定 `--target` 时 MUST 默认取仓库根。模块本身是文件时，其「单元」MUST 表示为空（页面显示「—」），MUST NOT 伪造为 0 或 1。

#### Scenario: 同一生成器画出不同层级

- **WHEN** 依次执行 `--target engines`、`--target engines/ae_harness`、`--target backend/apps`
- **THEN** 三节的模块集合分别变成 `engines` 的首层条目、7 个原语模块、12 个 Django app，且每节的数字只反映该层级

#### Scenario: 文件也是模块

- **WHEN** 目标目录的首层存在代码文件（如仓库根的 `run.py`）
- **THEN** 该文件 MUST 作为一个模块出现在三节中，其「单元」显示为「—」

#### Scenario: 不含代码的条目不算模块

- **WHEN** 目标目录下某个子目录不含任何代码文件（如只有缓存或资源）
- **THEN** 该条目 MUST NOT 出现在模块集合里

### Requirement: 每个产物必须有消费者

`data/` 下的每个产物 MUST 至少被一个消费者使用：页面通过 `<script src>` 加载，或作为生成器 `--check` 的比对基线。MUST NOT 产出「同一份数据的第二种序列化」这类无人读取的副本。

#### Scenario: 新增产物必须证明有消费者

- **WHEN** 生成器新增一个输出文件
- **THEN** 该文件 MUST 同时满足：被 `index.html` 加载，或在 `--check` 模式里被读取比对；两者都不满足时 MUST NOT 入库

#### Scenario: 无消费者的产物被清理

- **WHEN** 执行一次完整生成
- **THEN** `data/` 中 MUST NOT 存在既未被页面加载、也未被 `--check` 使用的文件

### Requirement: 离线可开

页面 MUST 在 `file://` 协议下双击即开，且 MUST NOT 依赖网络：无 CDN、无网络字体、无远程脚本、无 `fetch`。结构图 MUST 为手写 SVG；图表库 MUST 来自 `vendor/` 的本地副本。

#### Scenario: 断网双击打开

- **WHEN** 断开网络后双击 `index.html`
- **THEN** 三节全部正常渲染，控制台无 error / pageerror，无任何外部请求

#### Scenario: 数据以脚本方式加载

- **WHEN** 页面加载数据
- **THEN** MUST 通过 `<script src>` 加载 `data/viz.js`（脚本内是 JSON 载荷的包装），MUST NOT 使用 `fetch` 读取 JSON 或 CSV

### Requirement: 数字口径可追溯

每个展示的数字 MUST 能追到一条明确口径，且页面文案、README 口径表、生成器行为三处一致：

- 代码行 = 非空物理行（`.vue` 含 template/style）；
- 文件 = 代码文件数，排除 `__init__.py`、`__pycache__`、`migrations/`、`vendor/`、`logs/`、`temps/`、`data/`、`dev_docs/`、`node_modules/`；
- 单元 = 目录模块的直接子项数（子目录需含代码）；
- 依赖 = 一个文件对同一目标模块只计一次；
- 前端→后端是 **HTTP 调用**（`kind: http`，橙色虚线，量词「处」），不是 import，且只在模块集合同时含 `frontend` 与 `backend` 时出现。

#### Scenario: 页面数字与 CSV 一致

- **WHEN** 对照页面的代码量分布与 `data/code-stats.csv`
- **THEN** 每个模块的代码行、文件数、单元数与 CSV 对应行完全一致，合计等于各行之和

#### Scenario: 依赖量词与图例正确

- **WHEN** 查看依赖图的边标签与图例
- **THEN** import 边 MUST 标「条」、HTTP 边 MUST 标「处」，图例 MUST 写明橙色虚线是 HTTP 调用而非 import

### Requirement: 一次生成、单层级覆盖

重新采集 MUST 只需运行一次生成器，即写出页面需要的全部产物；页面自身 MUST NOT 扫描仓库、MUST NOT 运行时读取 CSV 或 JSON。生成 MUST 覆盖同一套产物，即一次只维护一个层级。

#### Scenario: 一次生成产出全部产物

- **WHEN** 运行生成器一次
- **THEN** 三份产物同时更新，无需第二次内联步骤

#### Scenario: 切换层级后页面自洽

- **WHEN** 用 `--target engines/ae_harness` 生成后刷新页面
- **THEN** 三节 MUST 全部反映该层级，页面脚注 MUST 显示该 target，MUST NOT 残留上一层级的数据

#### Scenario: 快照过期可检测

- **WHEN** 仓库代码已变更但未重新生成，运行生成器的 `--check` 模式
- **THEN** MUST 报告哪些产物已过期并以非零退出码结束；数据最新时以 0 退出，且比对 MUST 忽略快照时间字段

### Requirement: 架构与依赖不同源

架构图 MUST 来自每层级手写的一份 JSON（人工语义，代码无法检测），依赖图 MUST 来自静态解析。两者 MUST NOT 互相验证，MUST NOT 用一方的数字修改另一方。

#### Scenario: 依赖变化不篡改架构

- **WHEN** 依赖边数量变化后重新生成
- **THEN** 架构图的节点、连线与标签 MUST 保持不变（除非对应层级的架构 JSON 被修改）

#### Scenario: 缺配置只显示空态

- **WHEN** 生成时该层级没有 `config/architecture.<slug>.json`
- **THEN** 第 1 节 MUST 显示空态并提示应创建的文件路径，其余两节 MUST 正常渲染

### Requirement: 文档关系与原文可查

系统 SHALL 从仓库里的 `AGENTS.md` 与 `.agents/docs/**/*.md` 生成文档关系，MUST 包含三类边：

- **层级**：父 `AGENTS.md` → 子 `AGENTS.md`（按目录就近取父级）；
- **管辖**：`AGENTS.md` → 它所在的目录（根文档管整仓）；
- **引用**：`AGENTS.md` 里 markdown 链接指向的模块文档。

文档图 MUST 是全仓口径，MUST NOT 随 `--target` 变化。点击任一节点 MUST 在页面内显示该文档**全文**；正文 MUST 已内联在产物里，MUST NOT 依赖运行时读取文件（`file://` 下无 `fetch`）。

#### Scenario: 三类边齐全

- **WHEN** 打开第 4 节
- **THEN** 图中 MUST 出现每个 `AGENTS.md` 节点、每个模块文档节点与每个管辖目录节点；层级边数 = 子 AGENTS 数、管辖边数 = AGENTS 数、引用边数 = 索引里指向且存在的文档数

#### Scenario: 点节点看全文

- **WHEN** 点击任一文档节点
- **THEN** 右侧面板 MUST 显示标题、路径、大小/行数、管辖目录、出入链，并在 `<pre>` 里给出该文档全文；0 字节文档 MUST 显示「（空文件）」而不是空白

#### Scenario: 点管辖节点看归属

- **WHEN** 点击一个管辖目录节点（如 `backend/`）
- **THEN** 面板 MUST 列出所有管辖该目录的文档，并支持再点进正文

### Requirement: 版式冻结、变量随数据

页面版式（节顺序、条形图在左 / 环形图在右 / 明细表在下、表头与数字右对齐、`table-layout: fixed` 固定列宽、节点卡与配色、文档图左图右文）MUST 保持冻结；数据变化时 MUST 只改变节点数、数值与占比，MUST NOT 改变版式结构。

#### Scenario: 数据变化不改版式

- **WHEN** 模块数从 8 变成 7（换层级）后刷新页面
- **THEN** 条形图仍按代码行降序、环形图仍在右侧、明细表仍为 5 列，表头与数字右对齐（列左右边界差 < 1px）

#### Scenario: 占比与合计自洽

- **WHEN** 读取明细表的占比列与合计
- **THEN** 各模块占比之和 MUST 等于 100%（±0.1%），合计 MUST 等于条形图与环形图的数据之和
