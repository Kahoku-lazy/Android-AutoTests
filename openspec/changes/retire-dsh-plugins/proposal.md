## Why

`dsh-plugins/` 是 2026-09 期为「写完 `backend/apps/**/*.py` 后立刻跑一次边界检查并把提醒注入会话」引入的 DSH 宿主插件（`arch-gate`）加一个聚合 patch 层。它**从未进入任何 profile**：`~/.dsh/profiles/web/cordis.patch.yml` 是空数组 `[]`，`desktop` 那份也没有该条目，只有在命令行手工 `dsh web --patch dsh-plugins/patch.yml` 启动时才会挂载，实际使用频率为零。而它守着的那条检查（`python utils/gen_arch_stats.py --check-boundaries`）早已由 `python run.py check` 与 CI `ci-phase1.yml` 长期兜底，插件提供的只是「同一检查的实时版」。

留着它的代价是实打实的：仓库根多一条从不加载的 TypeScript 构建链（源码 + 必须单独 `npm run build` 的 `dist/`），每次 `backend/` 或 `utils/` 路径调整都要同步一处根本不生效的调用面（历史变更 `2026-10-21-move-dev-tools-to-utils`、`2026-10-21-backend-package-layout` 都为此各改了三处）。收益为零、维护面积非零，故整体退役。

## What Changes

- 删除整个 `dsh-plugins/` 目录：
  - `dsh-plugins/patch.yml`（聚合 patch 层，全文只有 `arch-gate` 一条）
  - `dsh-plugins/arch-gate/package.json`、`tsconfig.json`、`README.md`
  - `dsh-plugins/arch-gate/src/index.ts`、`src/node-stubs.d.ts`
  - 未跟踪的构建产物 `dsh-plugins/arch-gate/dist/`（`dist/index.js` 是唯一挂载入口）
- 清理两处失效引用：
  - `utils/gen_arch_stats.py` 模块 docstring 中「会让 CI 与 dsh-plugins/arch-gate（execFile 捕获 + passMarker "零违规"）误判失败」改为只描述「被管道/重定向捕获」这一通用触发条件，检查逻辑本身不动。
  - `dev_docs/project-viz/index.html` 顶层目录说明移除 `dsh-plugins（插件）` 一句。
- **不新增替代守卫**：模块边界仍由 `python run.py check`（`utils/check_gates.py` 的 `boundary` 项）与 CI `.github/workflows/ci-phase1.yml` 的 `gen_arch_stats.py --check-boundaries` 承担；失去的只是「写入后立刻在当前回合提醒」的实时反馈。
- 不改写 `openspec/changes/archive/**` 中提到 `dsh-plugins` 的历史记录——那是当时的真实事实。
- **BREAKING**（仅影响本地开发习惯）：任何 `dsh web --patch dsh-plugins/patch.yml` 或 `dsh --profile web --patch dsh-plugins/patch.yml --dump-config` 命令立即失效，需改为直接 `dsh web`。

## 关联文档

无。本变更为纯工具链资产退役，不涉及任何 PRD / ARCH 的需求编号变更；架构结论与模块边界规则均不变。

## Capabilities

### New Capabilities

（无：退役一个从不加载的开发期守卫，不产生任何对外可见的新行为。）

### Modified Capabilities

（无：`openspec/specs/` 下没有任何能力把「DSH 宿主插件」或「写入后实时边界提醒」写成对外行为契约——该守卫只是 `python run.py check` 与 CI 里同一条检查的重复实现。故本变更在 `.openspec.yaml` 声明 `skip_specs: true`，不为凑校验而虚构需求。）

## Impact

- **代码（TypeScript）**：删除 `dsh-plugins/arch-gate/src/**`（约 200 行）与其构建配置；`frontend/node_modules` 的 tsc 不再被它借用。
- **代码（Python）**：仅 `utils/gen_arch_stats.py` 一处注释文案，运行逻辑零改动。
- **配置**：无。`.gitignore`、`ruff.toml`、`pytest.ini`、`tach.toml` 均未引用该目录。
- **CI**：无改动。`ci-phase1.yml` 的四个 job 都不引用 `dsh-plugins/`。
- **宿主插件**：`arch-gate` 退役。`__DSH_HOME`/profile 无需清理——它本来就没被安装进 profile（`file:` 符号链接的备选安装方式同样未使用）。
- **文档**：`dev_docs/project-viz/index.html` 顶层目录说明一处。
- **测试范围**：不动任何用例（该插件无测试资产）。验收 = `python run.py check` 退出码 0 + 全仓 `dsh-plugins` / `arch-gate` 引用归零（`openspec/changes/archive/**` 历史除外）+ `dsh-plugins/` 目录不存在。
- **不影响**：`openspec/changes/archive/**` 历史记录；`utils/gen_arch_stats.py --check-boundaries` 的判定口径；模块边界红线与依赖方向（本变更不改任何规则条款）。
