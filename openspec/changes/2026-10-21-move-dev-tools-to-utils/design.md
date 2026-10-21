## Context

动机见 `proposal.md`。现状约束（实测）：

- 根 `tools/` 6 个文件：4 个 CLI 脚本 + 2 个 JSON 白名单。四个脚本都靠 `ROOT = Path(__file__).resolve().parent.parent` 定位仓库根，移到 `utils/` 后该表达式仍指向仓库根（同为一级子目录），无需改。
- 白名单路径是**硬编码**的相对路径：`gen_arch_stats.py` 里 `PROJECT_ROOT / "tools" / "boundary-whitelist.json"` 与 `PROJECT_ROOT / "tools" / "frontend-whitelist.json"`。
- 门禁命令由 `tools/check_gates.py` 以子进程方式拉起，命令串里带 `tools/...` 相对路径，cwd 默认 `ROOT`。
- 仓库外还有三处会拉起这些脚本：`run.py` 的 `check` 子命令、GitHub Actions 的 `ci-phase1.yml`、DSH 宿主插件 `dsh-plugins/arch-gate`（写 `apps/**/*.py` 后触发边界检查）。
- `utils/` 已存在且是**被业务代码 import 的包**（`utils/logs.py`，`utils/__init__.py` 声明「零 `apps.*`、零 `django.*`」）。
- `pytest.ini` 的 `testpaths = tests`，`utils/` 不进测试收集。

## Goals / Non-Goals

**Goals**

- 开发脚本的唯一位置变成 `utils/`，且移动后**命令行入口逐个实跑通过**。
- 仓库内不再存在指向 `tools/` 的可执行引用（历史归档单、`engines/agents/tools/` 除外，见 Non-Goals）。

**Non-Goals**

- 不改写 `openspec/changes/archive/**` 里的历史路径：那是「当时事实」，改写会伪造历史。
- 不动 `engines/agents/tools/`（智能体工具模块，与开发脚本是两回事）。
- 不重构脚本内部逻辑、不改任何门禁的判定口径与分级，不新增/删除检查项。
- 不把 `utils/` 纳入 ruff 门禁的 `PY_SCOPES`（那是另一件事，本变更只做归位）。

## Decisions

### D1 平铺进 `utils/`，不建 `utils/tools/`

- 选择：`utils/check_gates.py` 等，路径最短，`python utils/check_gates.py` 一眼可读。
- 备选 A（`utils/tools/`）：目录身份保留，但路径更长，且 `utils/tools` 与 `engines/agents/tools` 形成同名歧义。
- 备选 B（`scripts/` 新目录）：语义最正，但与用户「移到 utils」的裁定不符。
- 代价：`utils/` 同时装「库」与「CLI 脚本」，需在 `utils/__init__.py` 用 docstring 明确分区（库：`logs`；脚本：四个），并保证脚本不被 import 时不产生副作用。

### D2 `git mv` 保留文件历史

移动用 `git mv`，内容改动拆成独立提交点（移动 + 路径同步同一变更单内），避免出现「删除 + 新增」导致 blame 断链。

### D3 脚本入口保持「路径直跑」，不引入 `-m` 约定

`run.py` 与 CI 继续用 `python utils/<脚本>.py` 形式（与现状 `python tools/<脚本>.py` 一一对应，最小语义变化）。`python -m utils.live_screen` 仍可用（`utils` 是包），文档里的调试入口串统一改成它。

### D4 白名单路径改为 `PROJECT_ROOT / "utils" / "<name>.json"`

两个 JSON 跟随脚本一起移动，`gen_arch_stats.py` 内两处硬编码同步；`--check-boundaries` / `--check-frontend` 的提示文案里的路径也一并改，避免报错时把人指到不存在的目录。

### D5 ruff 豁免精确到四个脚本，而不是 `utils/**/*.py`

- 选择：`"utils/{check_gates,gen_arch_stats,check_openapi_coverage,live_screen}.py" = ["T201"]`。
- 理由：`T201`（禁止 `print`）的既有豁免口径是「CLI 入口 / 种子脚本」，`utils/logs.py` 是库，不该被顺带放开。
- 不动 `lint.isort.known-first-party`：`utils` 已被大量业务代码 import，若此时把它加进 first-party 会触发全仓 `I001` 重排，属于本变更之外的噪音；`tools` 条目留在配置里无害（已无代码 import 该包），删除与否不影响检查结果，故**不动**。

### D6 `.gitignore` 的 `tools/_tmp*` 换成 `utils/_tmp*`

这两行是「临时脚本不入库」的约定，随目录一起迁移；否则以后在 `utils/` 里放临时脚本会被误提交。

### D7 不留 `tools/` 兼容垫片

- 备选：保留 `tools/check_gates.py` 作为转发脚本。
- 否决理由：全仓可执行引用只有 10 处，一次改净；留垫片会让「工具到底在哪」继续含糊，且垫片自身要维护、还会被 `--check-boundaries` 当作新文件扫描。
- 代价：本地/外部习惯用法失效，已在 `proposal.md` 标 **BREAKING**，并在 `README.md` 与 `AGENTS.md` 写明新入口。

### D8 模板文件必须改

`openspec/schemas/android-autotests/templates/tasks.md` 内含 `python tools/gen_arch_stats.py --check-boundaries` 之类的验收命令；不改会让**之后每一张变更单**都写出失效命令，属于会持续扩散的坑。

## Risks / Trade-offs

- [插件 `arch-gate` 硬编码路径改错 → 写入守卫静默失效] → 改完后复刻插件真实调用（`execFile("python", ["utils/gen_arch_stats.py", "--check-boundaries"], {cwd: 仓库根})`）实测，断言输出含「零违规」且无 Traceback。
- [CI 里漏改某条命令 → 该 job 变成「找不到文件」红项] → 改完全文 grep `tools/` 只剩历史归档与 `engines/agents/tools/`；并本地 `python run.py check` 跑一遍对应 job 的门禁项。
- [`utils/` 不在门禁 ruff 扫描范围内 → 移动后的脚本可能带着格式/lint 问题进主干] → 实施时本地跑 `python -m ruff check utils/` 与 `python -m ruff format --check utils/`（一次性的范围外自检，不写进门禁）。
- [脚本被 `utils` 包导入路径影响（如 `python -m utils.check_gates` 触发 `__init__`）] → `utils/__init__.py` 保持零 import、零副作用，仅在 docstring 登记。
- [并发会话正在改仓库] → 本次只动上述文件，逐文件 `git add`，不碰 `apps/`、`frontend/` 与其它会话的改动。

## Migration Plan

1. `git mv` 6 个文件到 `utils/`，删除空掉的 `tools/` 目录。
2. 改脚本内部自引用（白名单路径、用法串、`prog=` 名）。
3. 改调用面：`run.py`、`check_gates.py` 的 3 条子进程命令、`ci-phase1.yml`（4 命令 + 1 注释）、`dsh-plugins/patch.yml`、`dsh-plugins/arch-gate/{src/index.ts,README.md}`。
4. 改配置：`ruff.toml`、`.gitignore`。
5. 改文档 5 处：`AGENTS.md`、`README.md`、`apps/自测与检测指令.md`、`dev_docs/ARCH_PRD/ARCH-平台架构设计.md`、`openspec/schemas/android-autotests/templates/tasks.md`。
6. 验证：四个脚本各自 `--help`/`--list` 实跑；`python utils/check_gates.py --only boundary,openapi-coverage,vue-file-size,silent-except`；`python run.py check`；插件调用复刻。
7. **回滚**：本变更为单提交（或单 change 的一组提交），`git revert <commit>` 即可整体回退；目录移动不涉及数据迁移。

## Open Questions

（无）
