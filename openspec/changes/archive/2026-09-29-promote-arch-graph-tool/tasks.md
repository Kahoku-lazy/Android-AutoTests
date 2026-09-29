## 1. 外置声明层

- [x] 1.1 新增 `tools/arch_graph/declarations.json`：把临时脚本里的硬编码声明（PRD 路径、功能域→代码文件/符号、规格→功能域、数据表、测试扫描范围、产物目录与文件名）搬进来，结构为 `{schema_version, out_dir, scopes:[...]}`；验证：`python -c "import json;json.load(open('tools/arch_graph/declarations.json',encoding='utf-8'))"` 无异常
- [x] 1.2 声明里的每条代码锚点逐个核对存在（路径 + 符号名）；验证：重跑后无新增断锚，锚点重放结果与 demo 期逐项一致（断锚仍为那 1 处既有数据）

## 2. 转正生成器

- [x] 2.1 新增 `tools/gen_arch_graph.py`：从声明文件读 scope，扫描需求侧（PRD 小节 / 规格 Requirement / Scenario）、代码侧（文件 / 符号 / 路由 / 表）、测试侧（文件 + 规格锚点），建图并重放锚点；验证：`python tools/gen_arch_graph.py --only json` 产出 JSON，节点/边数与 demo 期一致（**160 / 262**）
- [x] 2.2 CLI 支持 `--scope` · `--only {all,json,workbench,doc}` · `--out-dir` · `--quiet`；验证：四种 `--only` 取值各跑一次，产物路径与提示正确；相对 `--out-dir` 落到指定目录
- [x] 2.3 生成后做结构自检（每条边两端都在节点表、健康度计数与节点表一致），不自洽则非 0 退出；验证：注入一条指向不存在节点的边 → `main()` 返回 1 并打印 `✗ 边 e1 的终点不存在: nope`；正常图问题数为 0
- [x] 2.4 工具代码不含任何文档路径：产物目录与文件名一律从声明文件读；验证：`tools/gen_arch_graph.py` 中 `dev_docs` 命中 0

## 3. 转正页面模板

- [x] 3.1 `tools/arch_graph/templates/workbench.html`：从 `temps/arch_graph/workbench.template.html` 移入，占位符保持 `__GRAPH_JSON__`；验证：注入后页面自检 36 项全过
- [x] 3.2 `tools/arch_graph/templates/doc.html`：从 `temps/arch_graph/viewer.template.html` 移入，页脚改为指向 `tools/gen_arch_graph.py`；验证：注入后页面自检 15 项全过
- [x] 3.3 产物落位与改名：JSON 改 `arch-graph-login.json`（去掉 demo），两个页面路径不变；验证：目录内已无 `arch-graph-login.demo.json`

## 4. 验证

- [x] 4.1 一条命令重建全部产物（`python tools/gen_arch_graph.py`）；验证：三份产物落盘，顶栏统计与 JSON 一致（160 卡片 / 262 连线）
- [x] 4.2 工作台页面自检（Playwright，36 项：载入 / 缩放 / 拖动保存 / 筛选 / 详情 / 导入导出）；验证：输出「全部通过」
- [x] 4.3 文档页自检（Playwright，15 项）；验证：输出「全部通过」
- [x] 4.4 `ruff check` + `ruff format --check` 覆盖新增 Python 文件；验证：`All checks passed!` / `1 file already formatted`

## 5. 收尾

- [x] 5.1 删除 `temps/arch_graph/` 里已转正的生成器与模板（`build_graph.py` / `render_html.py` / `render_workbench.py` / 两个 `*.template.html`），只留自检脚本与截图；验证：模板与声明在 `tools/arch_graph/` 下只有一份
- [x] 5.2 `DEV_DOCS_README.md` 补工具用法（命令速查）与「实现归属变化」同步行；验证：文件中可检索到 `tools/gen_arch_graph.py`
- [x] 5.3 全仓无 `arch-graph-login.demo` 残留引用；验证：`grep` 0 命中
