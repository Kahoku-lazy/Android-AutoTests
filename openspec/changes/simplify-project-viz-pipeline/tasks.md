## 1. 基线对账（先锁数字，再动代码）

- [x] 1.1 记录旧实现的 project 模块级数字作为对账基线；验证：`temps/viz-baseline-project.json` 存在，含 frontend 41,745 / backend 22,575 / engines 11,268 / tests 7,923 / utils 4,450（合计 87,961）
- [x] 1.2 记录清理前 `data/` 体积与文件清单；验证：旧目录 8 个文件、合计 672.6KB，记入 `temps/viz-baseline-project.json` 的 `diff` 段

## 2. 生成器重写（新文件，不原地改）

- [x] 2.1 新建 `dev_docs/project-viz/tools/gen_viz_data.py`：模块头 4 字段 + 扫描助手（遍历 / 非空行 / 跳过规则），单函数 ≤ 40 行；验证：AST 统计每个函数行数与圈复杂度，全部 ≤ 40 行 / ≤ 12
- [x] 2.2 实现模块采集：`--target` 目录首层条目（目录或代码文件）→ `{module, loc, files, units}`，文件模块 units 为空；验证：`--target .` 得 8 行、`--target engines/ae_harness` 得 7 行、`--target backend/apps` 得 12 行
- [x] 2.3 实现依赖采集：点分名 → 模块索引（绝对 + 相对导入），前后端并存时补 HTTP 边；验证：`.` 得 9 条边（含 frontend→backend 98 处）、`engines/ae_harness` 得 2 条、`backend/apps` 得 20 条
- [x] 2.4 实现写盘：`data/code-stats.csv` / `data/dependencies.json` / `data/viz.js`（合成 `window.__VIZ__`，arch 读 `config/architecture.<slug>.json`）；验证：`node --check dev_docs/project-viz/data/viz.js` 退出 0
- [x] 2.5 实现 `--check`：比对 CSV / deps / viz.js 且忽略 `generated_at`；验证：生成后 `--check` 退出 0，改一行数据后退出 1

## 3. 配置目录（架构手写）

- [x] 3.1 新建 `config/architecture.repo-root.json`：迁移旧 `data/architecture.json` 的 11 组件 / 10 连线 / 1 边界 / 3 结论卡，并补 `row`/`col`；验证：生成后 `viz.js` 的 `arch.components` 长度为 11、`connections` 为 10
- [x] 3.2 缺配置时给空态而不是编造：验证：`--target engines` 生成后 `viz.js` 的 `arch` 为 `null`，页面第 1 节显示空态提示路径

## 4. 页面接线（版式冻结，节点位置数据驱动）

- [x] 4.1 数据入口由 `window.MINI` 改为 `window.__VIZ__`，并加载 `data/viz.js`；验证：`index.html` 内不再出现 `window.MINI` / `data.js`
- [x] 4.2 架构图位置改为 `row`/`col` 驱动、依赖图改网格布局（避免任意层级丢节点）；验证：`--target backend/apps` 的 12 个节点全部出现在 SVG 中
- [x] 4.3 页脚显示当前 target 与快照时间；修正原第 73 行不存在的命令（`temps.viz_min.gen_data`）为真实命令；验证：页面文案与 README 更新命令逐字一致
- [x] 4.4 内联脚本语法检查：抽取 `<script>` 内容写 `temps/viz-inline.js` 后 `node --check`；验证：退出 0（236 行）

## 5. 清理旧链路

- [x] 5.1 删除 `tools/gen_board_data.py`、`tools/gen_arch_data.py`、`gen_data.py`、`data/{board,history}.{json,js}`、`data/architecture.{json,js}`、`data/code-relations.csv`、根 `data.js`；验证：目录仅剩 `index.html`、`README.md`、`AGENTS.md`、`tools/{gen_viz_data.py,count_frontend.mjs}`、`config/`、`data/`（3 份）、`vendor/echarts.min.js`
- [x] 5.2 全目录确认无残留引用；验证：`window.MINI` / `gen_board_data` / `gen_data.py` / `code-relations` / `board.json` / `history.js` 均无命中（README/AGENTS 的历史说明除外）
- [x] 5.3 体积复核：`data/` 从 672.6KB 降到 5.4KB（-99.2%），三份产物分别被页面加载或 `--check` 使用

## 6. 文档同步

- [x] 6.1 重写 `README.md`：三节表、`--target` 模块示例、一条命令更新、产物契约、架构 JSON schema、边界；验证：README 里每条命令实跑通过
- [x] 6.2 更新 `AGENTS.md`：数据流图、目录职责、模块与口径、已知坑、自检；验证：红线 1–7 条款文字逐条比对，语义无放宽（仅红线 5 的实现描述改为 `viz.js` 外壳）
- [x] 6.3 三处口径一致：生成器 docstring、页面文案、README 口径表；验证：依次读三处，代码行 / 文件 / 单元 / 依赖 / HTTP 量词定义一致

## 7. 第 4 节：AGENTS 文档关系（追加）

- [x] 8.1 生成器扫全仓文档：所有 `AGENTS.md`（含 `.agents/`、`dev_docs/`）+ `.agents/docs/**/*.md`，排除依赖/临时/缓存目录；验证：`--check` 报告「文档 58 篇」
- [x] 8.2 三类关系：层级（近祖先 AGENTS）、管辖（文档所在目录）、引用（markdown 链接指向的文档）；验证：`docs.js` 里 hierarchy 7 / governs 8 / references 49，路径节点 8，无孤儿
- [x] 8.3 产物 `data/docs.js`：全文内联 + `--check` 忽略 `generatedAt` 比对；验证：`node --check dev_docs/project-viz/data/docs.js` 退出 0，重复 `--check` 稳定
- [x] 8.4 页面第 4 节：泳道图（左）+ 正文面板（右），点节点看全文、点管辖节点看归属、点出入链跳转；验证：`node temps/viz-page-check.mjs` 断言文档图节点 65 个、含根文档与管辖节点、面板有 `<pre>` 正文
- [x] 8.5 文档与数据解耦：文档图不随 `--target` 变；验证：`--target engines/ae_harness` 后文档图节点仍为 65、正文仍可读
- [x] 8.6 README / AGENTS 同步四节结构、`docs.js` 产物、文档图口径与「200KB 是故意的」；验证：README 四视图表与页面 h2 逐条对应

## 8. 验收

- [x] 7.1 `--check` 稳定性：默认层级生成 → 检查通过 → 换层级再切回；验证：两次 `--check` 均退出 0
- [x] 7.2 改动范围复核：验证：本变更只新增/修改 `dev_docs/project-viz/` 与 `openspec/changes/simplify-project-viz-pipeline/`
- [x] 7.3 无浏览器逻辑自检：用 `node:vm` 跑 `viz.js` + 内联脚本、stub `document`/`echarts`，断言三节产物；验证：`node temps/viz-page-check.mjs` 在 `.` / `backend/apps` 两级均退出 0（架构 11 节点 / 依赖 8 节点 9 边 / 表格 8 行 / 合计 82,575；`backend/apps` 12 节点 20 边，第 1 节为空态）
- [ ] 7.4 浏览器验收（需人工）：`file://` 双击与 `http://127.0.0.1:8811` 各开一次，确认三节视觉正常、零 console error、断网可用、表头与数字右对齐、卡片微倾；验证：截图或 DevTools 记录
