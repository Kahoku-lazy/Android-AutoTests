## 1. 目录迁移

- [x] 1.1 `git mv tools/check_gates.py utils/check_gates.py`、`tools/gen_arch_stats.py utils/gen_arch_stats.py`、`tools/check_openapi_coverage.py utils/check_openapi_coverage.py`、`tools/live_screen.py utils/live_screen.py`。验证：`git status --short` 中四项显示为 `R`（重命名）而非 `D`+`??`。
- [x] 1.2 `git mv tools/boundary-whitelist.json utils/boundary-whitelist.json`、`tools/frontend-whitelist.json utils/frontend-whitelist.json`；`tools/` 变空后删除该目录。验证：`Test-Path tools` 为 False，`utils/` 下 6 个文件齐全。

## 2. 脚本内自引用

- [x] 2.1 `utils/gen_arch_stats.py`：两处白名单路径 `PROJECT_ROOT / "tools" / ...` 改为 `"utils"`（`boundary-whitelist.json`、`frontend-whitelist.json`），提示文案里 `tools/boundary-whitelist.json`、`tools/frontend-whitelist.json` 同步。验证：`python utils/gen_arch_stats.py --check-boundaries` 退出码 0 且输出「零违规」，不再出现「白名单缺失」类报错。
- [x] 2.2 `utils/gen_arch_stats.py` 与 `utils/check_openapi_coverage.py` 的模块 docstring 用法串由 `python tools/...` 改为 `python utils/...`。验证：`Select-String -Path utils\*.py -Pattern 'tools'` 命中 0（`gen_arch_stats.py` 里对 `apps/ai_assistant/tools.py` 注册表的说明属同名不同物，按上下文保留，需在结果里逐条说明）。
- [x] 2.3 `utils/check_gates.py`：`openapi-coverage` / `boundary` / `vue-file-size` 三条 `cmd_gate` 的命令串改指 `utils/...`，模块 docstring 与 `--only` 示例同步。验证：`python utils/check_gates.py --only openapi-coverage,boundary,vue-file-size` 全绿。
- [x] 2.4 `utils/live_screen.py`：四处 `python -m tools.live_screen` 用法串与 `prog=` 名改为 `utils`。验证：`python -m utils.live_screen --list` 能执行并以「未连接设备」类提示结束（非 `ModuleNotFoundError`），`--help` 显示的 prog 名为 `python -m utils.live_screen`。

## 3. 调用面与配置

- [x] 3.1 `run.py`：`check` 子命令的 `ROOT / "tools" / "check_gates.py"` 改为 `"utils"`，L10 用法注释同步。验证：`python run.py check` 退出码 0（阻塞项全绿）。**实测**：`run.py check` 已从 `utils/check_gates.py` 正常拉起并跑完 24 项；阻塞 20/22 PASS，2 项红均为**并发会话未提交文件**（`ruff-format` → `apps/report_generator/views.py`；`prettier` → `report-generator` 3 个 vue + `task-list/TaskDetailPage.vue`），与本变更文件无交集；本变更涉及的 `openapi-coverage`/`boundary`/`vue-file-size`/`silent-except` 全 PASS。
- [x] 3.2 `.github/workflows/ci-phase1.yml`：4 条命令行（`check_gates.py --only openapi-schema,openapi-coverage`、`check_gates.py --only silent-except`、`gen_arch_stats.py --check-boundaries`、`gen_arch_stats.py --check-frontend`）与 1 条注释同步改为 `utils/`。验证：`Select-String -Path .github\workflows\*.yml -Pattern 'tools/'` 命中 0；YAML 仍可解析（`python -c "import yaml,pathlib;yaml.safe_load(pathlib.Path('.github/workflows/ci-phase1.yml').read_text(encoding='utf-8'))"`）。
- [x] 3.3 `dsh-plugins/patch.yml`、`dsh-plugins/arch-gate/src/index.ts`（2 处 args/注释）、`dsh-plugins/arch-gate/README.md`（2 处）改为 `utils/gen_arch_stats.py`。验证：`Select-String -Path dsh-plugins -Include *.yml,*.ts,*.md -Recurse -Pattern 'tools/gen_arch_stats'` 命中 0。
- [x] 3.4 插件真实调用路径复刻：临时脚本按 `arch-gate/src/index.ts` 的 `execFile("python", ["utils/gen_arch_stats.py", "--check-boundaries"], {cwd: 仓库根})` 实跑（脚本放 `temps/`）。验证：stdout/stderr 含「零违规」、无 `Traceback`、退出码 0。
- [x] 3.5 `ruff.toml`：`"tools/**/*.py" = ["T201"]` 改为精确到四个脚本的 `"utils/{check_gates,gen_arch_stats,check_openapi_coverage,live_screen}.py"`；`.gitignore` 的 `tools/_tmp*/`、`tools/_tmp_*.py` 改为 `utils/`。验证：`python -m ruff check utils/` 与 `python -m ruff format --check utils/` 通过；`Select-String -Path ruff.toml,.gitignore -Pattern 'tools/'` 命中 0。

## 4. 文档同步

- [x] 4.1 `utils/__init__.py` docstring 登记「库：`logs`；CLI 脚本：四个 + 两个白名单 JSON」，并写明包本身保持零 import 零副作用。验证：`python -c "import utils; print('ok')"` 无输出副作用；`python -m ruff check utils/__init__.py` 通过。
- [x] 4.2 `AGENTS.md`（「检查清单与判定口径以 `tools/check_gates.py` 为唯一真相源」）与 `README.md`（目录表 `tools/` 行、门禁说明两处）改为 `utils/`。验证：`Select-String -Path AGENTS.md,README.md -Pattern 'tools/(check_gates|gen_arch_stats)'` 命中 0。
- [x] 4.3 `apps/自测与检测指令.md`（3 处命令）、`dev_docs/ARCH_PRD/ARCH-平台架构设计.md`（3 处）改为 `utils/`。验证：两文件 `tools/gen_arch_stats` 命中 0；ARCH 文档的统计数字与结论未改（`git diff` 只含路径）。
- [x] 4.4 `openspec/schemas/android-autotests/templates/tasks.md`：验收命令里的 `python tools/gen_arch_stats.py ...` 改为 `utils/`；`openspec/changes/archive/**` 不动。验证：模板内 `tools/gen_arch_stats` 命中 0；`git status --short openspec/changes/archive` 无改动。

## 5. 验证与关单

- [x] 5.1 全仓可执行引用归零检查。验证：`Select-String -Path . -Include *.py,*.toml,*.yml,*.yaml,*.md,*.ts,*.mjs,*.js -Recurse -Pattern 'tools/(check_gates|gen_arch_stats|check_openapi_coverage|live_screen|boundary-whitelist|frontend-whitelist)'` 的命中只剩 `openspec/changes/archive/**` 与 `tools.py`（`apps/ai_assistant/tools.py` 注册表说明），逐条说明。
- [x] 5.2 本地门禁：`python run.py check` 退出码 0。验证：输出「阻塞项全部通过」；若因**其它会话**既存问题红项，需在结果中标注归属并单独举证本变更文件无违规。**实测**：阻塞 20/22 PASS；2 项红项文件 = `apps/report_generator/views.py` + `frontend/src/modules/report-generator/{CaseBreakdown,index,ReportDetail}.vue` + `frontend/src/modules/task-list/TaskDetailPage.vue`，全部落在并发会话的 `git status` 改动集内；本变更 20 个文件不在该 2 项检查范围内（`utils/` 不在 `PY_SCOPES`，prettier 只扫 `frontend/src`），且 `python -m ruff check utils/` 与 `ruff format --check utils/` 均通过。
- [x] 5.3 四个脚本入口冒烟：`python utils/check_gates.py --help`、`python utils/gen_arch_stats.py --check-boundaries`、`python utils/check_openapi_coverage.py`、`python utils/live_screen.py --list`。验证：四条均以预期退出码结束，无 `ModuleNotFoundError` / `FileNotFoundError`。
- [ ] 5.4 `openspec validate 2026-10-21-move-dev-tools-to-utils --strict` 通过；逐文件 `git add` 本变更改动面（`utils/`、`run.py`、`ruff.toml`、`.gitignore`、CI、`dsh-plugins/`、上述文档）后提交，**禁止 `git add -A`**。验证：`git status --short` 中除本变更文件外无我引入的改动；`git log -1 --stat` 文件清单与本变更 Impact 段一致。
