## Why

「需求 × 代码 关系图」的 demo 已经跑通（登录模块 160 节点 / 262 条边，工作台页面可载入 JSON、缩放、拖动卡片并记住位置、按功能模块筛选），但它的生成器、页面模板和声明数据现在全部住在 `temps/` —— 那是 gitignore 的临时目录，随时会被清理，换台机器就重建不出来；其中「哪个功能域由哪些文件实现」的人工声明更是硬编码在临时脚本里，既无法评审也无法版本化。

## What Changes

- 扫描器/生成器转正为 `tools/gen_arch_graph.py`：一条命令重建「关系图 JSON + 工作台页面（+ 文档页）」。
- 人工声明层外置为 `tools/arch_graph/declarations.json`（可版本化、可评审、可增量补模块），工具代码里不再有任何硬编码的功能域→代码映射。
- 页面模板移入 `tools/arch_graph/templates/`：`workbench.html`（工作台，主产物）与 `doc.html`（方案文档页）。
- 产物落到 `dev_docs/DEV_TEST/设计方案与报告/` 的现有位置，文件名去掉 `demo` 字样。
- **本轮不做检查能力**：不新增 `--check`、不改 `tools/check_gates.py`、不接 CI，断锚只作为图里的数据呈现，不拦任何提交。

## 关联文档

- 无 PRD 关联：工具链变更，不改任何平台行为与接口。
- 依据 ARCH-00 的开发工具口径与 `DEV_DOCS_README.md` 的工具登记表。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 工具链变更（新增开发工具 + 页面模板），无需求级行为变化；`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 新增：`tools/gen_arch_graph.py` · `tools/arch_graph/declarations.json` · `tools/arch_graph/templates/{workbench,doc}.html`
- 产物：`arch-graph-login.json` · `设计方案-需求与代码关系图工作台.html` · `设计方案-需求与代码关系图（登录模块Demo）.html`
- 不动 `apps/` · 前端 · 数据库 · 接口；不改门禁与 CI；`temps/arch_graph/` 只留自检脚本
- 测试范围：工具实跑（生成 JSON + 两个页面）· 两个页面 Playwright 自检 · 新增文件的 `ruff check` / `ruff format --check`
