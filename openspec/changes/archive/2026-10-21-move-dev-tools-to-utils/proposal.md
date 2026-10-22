## Why

仓库根目录同时存在 `tools/`（门禁、架构统计、投屏等开发脚本）与 `utils/`（平台公共基础设施包），两个目录职责都是「非业务的通用件」，长期并存会让「新脚本放哪」每次都要重新判断，也让 `utils/` 的边界声明（`utils/__init__.py` 写的是「公共基础设施包」）无法覆盖实际的通用工具。本变更把开发脚本统一收进 `utils/`，按用户裁定**平铺**落位。

## What Changes

- 移动（git 重命名，内容保持可用）：
  - `tools/check_gates.py` → `utils/check_gates.py`
  - `tools/gen_arch_stats.py` → `utils/gen_arch_stats.py`
  - `tools/check_openapi_coverage.py` → `utils/check_openapi_coverage.py`
  - `tools/live_screen.py` → `utils/live_screen.py`
  - `tools/boundary-whitelist.json` → `utils/boundary-whitelist.json`
  - `tools/frontend-whitelist.json` → `utils/frontend-whitelist.json`
  - 移动后删除空的 `tools/` 目录
- 脚本内自引用同步：`gen_arch_stats.py` 读白名单的两个路径、四份脚本的 `python tools/xxx.py` 用法串与 `python -m tools.live_screen` 调试入口串。
- 调用面同步：`run.py`（本地门禁入口）、`tools/check_gates.py` 内 3 条子进程命令、`.github/workflows/ci-phase1.yml`（4 条命令 + 1 条注释）、`dsh-plugins/patch.yml`、`dsh-plugins/arch-gate/src/index.ts`、`dsh-plugins/arch-gate/README.md`。
- 配置同步：`ruff.toml` 的 `per-file-ignores` 从 `tools/**/*.py` 改为 `utils/` 下这四个脚本（保住「CLI 脚本允许 print」的既有豁免）；`.gitignore` 的 `tools/_tmp*` 两行改为 `utils/_tmp*`。
- 文档同步：`AGENTS.md`、`README.md`、`apps/自测与检测指令.md`、`dev_docs/ARCH_PRD/ARCH-平台架构设计.md`、`openspec/schemas/android-autotests/templates/tasks.md` 中的 `tools/<脚本>` 路径。
- `utils/__init__.py` 的 docstring 补齐「四个开发脚本 + 两个白名单」的登记与「脚本仅供 CLI 调用、包本身保持零依赖零副作用」的口径。
- **BREAKING**（仅对仓库内调用方）：任何仍写 `python tools/check_gates.py` 或 `python -m tools.live_screen` 的本地习惯、脚本、CI 片段都会失效，必须改用 `utils/` 前缀。

## 关联文档

无。本变更为纯工具链目录归位，不涉及任何 PRD / ARCH 的需求编号变更（ARCH-平台架构设计.md 只改工具路径，不改架构结论）。

## Capabilities

### New Capabilities
（无：目录归位不产生新的能力需求，验收标准由门禁命令自身承担。）

### Modified Capabilities
（无：`openspec/specs/` 下没有任何能力描述「开发脚本位于 `tools/`」，本次不改变任何对外行为；故在 `.openspec.yaml` 声明 `skip_specs: true`。）

## Impact

- **代码（Python）**：`run.py`、`utils/__init__.py`、四个被移动脚本；`apps/`、`engines/`、`gateway/`、`config/`、`shared/` 业务代码**零改动**。
- **配置**：`ruff.toml`、`.gitignore`。
- **CI**：`.github/workflows/ci-phase1.yml` 的 `backend-check` / `static-checks` / `boundary-check` / `frontend-quality` 四个 job 内的命令行。
- **宿主插件**：`dsh-plugins/arch-gate`（每次写 `apps/**/*.py` 后调用边界检查）与 `dsh-plugins/patch.yml`，改错会让写入守卫静默失效，需实测。
- **文档**：`AGENTS.md`、`README.md`、`apps/自测与检测指令.md`、`dev_docs/ARCH_PRD/ARCH-平台架构设计.md`、`openspec/schemas/android-autotests/templates/tasks.md`。
- **测试范围**：不动任何用例；验收 = `python run.py check` 全绿 + 四个脚本的命令行入口实跑 + 插件真实调用路径复刻。
- **不影响**：`engines/agents/tools/`（智能体工具模块）保持不动；`openspec/changes/archive/**` 的历史记录不改写（历史路径作为当时事实保留）。
