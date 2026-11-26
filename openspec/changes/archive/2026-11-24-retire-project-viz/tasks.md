## 1. 退役目录

- [x] 1.1 删除 `dev_docs/project-viz/` 整目录（53 个文件）。验证：`(Get-ChildItem dev_docs/project-viz -Recurse -File).Count` = 0 且目录不存在；`git status` 显示 53 个 `D`。
- [x] 1.2 确认 `dev_docs/` 下其余目录未受影响。验证：`Get-ChildItem dev_docs -Directory` 仍列出 `ARCH_PRD` / `DEV_TEST` 等原有目录。

## 2. 清配置例外

- [x] 2.1 `.gitignore`：删除放行 `dev_docs/project-viz/index.html` 与 `!dev_docs/project-viz/html/*.html` 的两条反选规则。验证：`.gitignore` 内 `project-viz` 命中 0；`dev_docs/**/*.html` 的全局忽略仍保留。
- [x] 2.2 `ruff.toml`：删除 `"dev_docs/project-viz/tools/sync_sidebar.py" = ["T201"]` 这一条 per-file-ignore。验证：`ruff.toml` 内 `project-viz` 命中 0；`python -m ruff check --no-cache .` 能正常解析配置（退出码非配置错误）。

## 3. 技能改述（去「参考实现」绑定，保留方法论）

- [x] 3.1 `.agents/skills/repo-viz-board/SKILL.md`：删掉「参考实现：本仓库 `dev_docs/project-viz/`（六个页面 + 生成器 + 图表底层）」整句，保留其后「不要照抄它的模块名——模块边界由当前仓库目录结构决定」这条原则。验证：该文件 `project-viz` 命中 0，且该原则句仍在。
- [x] 3.2 `.agents/skills/repo-viz-board/evals/evals.json`：把点名该目录的评测提示词改为不依赖具体目录的同类场景（如「这个代码可视化看板里的 agents 页，能不能加一个和上次比的功能…」），语义与考察点不变。验证：该文件 `project-viz` 命中 0；JSON 可被解析。
- [x] 3.3 `.agents/skills/repo-viz-board/assets/template/README.md`：把「见 `dev_docs/project-viz/ae-harness.js` 的实现」改为不指具体仓库路径的表述（如「见生成产物中的 `ae-harness.js` 实现」）。验证：该文件 `project-viz` 命中 0。
- [x] 3.4 `.agents/skills/arch-diagram-lite/SKILL.md`：删掉「参考实现：`dev_docs/project-viz/index.html` 第 1 节…」整句；`references/decomposition.md` 的链接若仅指向该句则同步调整。验证：该文件 `project-viz` 命中 0，且技能仍给出可执行的图语法说明。
- [x] 3.5 `.agents/skills/arch-diagram-lite/references/decomposition.md`：把拿 `gen_board_data.py` 作对照的那一格改为不含该文件名的表述（保留「看板数字由生成器产出、边必须能追到 AST」这一判定要点）。验证：该文件 `project-viz` 与 `gen_board_data` 命中均为 0。

## 4. 修路径夹具

- [x] 4.1 `.agents/skills/engines-docstring-check/scripts/selftest.py` 的 `SCOPE_CASES`：把 `("dev_docs/project-viz/tools/a.py", False, "顶层目录")` 换成仍存在的顶层目录路径（`("dev_docs/ARCH_PRD/a.py", False, "顶层目录")`）。验证：该文件 `project-viz` 命中 0；`python .agents/skills/engines-docstring-check/scripts/selftest.py` 全绿。

## 5. 保留项登记

- [x] 5.1 确认未改 `dev_docs/DEV_TEST/REVIEW-Agent文档审计复核与修复方案.md`（历史审计，提到 `project-viz/AGENTS.md:169` 属当时事实）。验证：`git status` 不含该文件。
- [x] 5.2 确认未改 `openspec/changes/repo-wide-python-docstring/design.md`（他人变更产物）。验证：`git status` 不含该文件。
- [x] 5.3 确认未碰仓库根 `result.json` 与 `_acl-recovery/`。验证：`git status` 不含它们。

## 6. 门禁与关单

- [x] 6.1 全仓复扫：`project-viz` 在 `.gitignore` / `ruff.toml` / `.agents/skills` 内命中 0；在 `dev_docs/DEV_TEST` 与 `openspec/changes/archive` 内的残留属历史记录，登记保留。验证：复扫输出贴进关单。
- [x] 6.2 `python -m run check` 通过（文档类变更不涉前后端构建，但仍跑项目门禁）。验证：退出码 0；若失败逐条判断是否既存。
- [x] 6.3 关单汇报：删除规模、8 处清理清单、保留项与理由、WIP 分支上 `simplify-project-viz-pipeline` 随之作废的声明、替代路径（轻量图/临时脚本）。随后归档（`skip_specs: true`）。
