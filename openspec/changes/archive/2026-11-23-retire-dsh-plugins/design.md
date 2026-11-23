## Context

`dsh-plugins/` 目前只有 `arch-gate` 一个插件，外加一个只含它一条的聚合 patch 层 `patch.yml`。挂载方式是 DSH 启动器的 `--patch` 覆盖层：`name: ./arch-gate/dist/index.js` 相对进程 cwd 解析，代码完全不进 `$DSH_HOME`。

删除前已实测的三条事实（决定「删了不会伤到正在跑的东西」）：

- `~/.dsh/profiles/web/cordis.patch.yml` 内容为 `[]`，`~/.dsh/profiles/desktop/cordis.patch.yml` 里没有 `arch-gate` 条目 → 它从未被装进任何 profile。
- 当前 GUI 由桌面版启动，未带 `--patch dsh-plugins/patch.yml` → 本会话没有加载该插件。
- 它守着的那条命令 `python utils/gen_arch_stats.py --check-boundaries`，在 `utils/check_gates.py`（`run.py check` 的 `boundary` 项）与 `.github/workflows/ci-phase1.yml` 里各有一份同样的调用。

## Goals / Non-Goals

**Goals:**

- 让「从不加载的构建链」与它带来的路径同步面从仓库消失：删除 `dsh-plugins/` 全部内容（含未跟踪的 `dist/`）。
- 删除后仓库内 `dsh-plugins` / `arch-gate` 的可执行引用归零（`openspec/changes/archive/**` 历史记录除外）。
- 保持模块边界检查的覆盖不变：`python run.py check` 与 CI 仍然跑同一条检查。

**Non-Goals:**

- 不引入任何替代的实时写后守卫：不加 DSH 新插件、不加 pre-commit、不加 git hook。
- 不改 `utils/gen_arch_stats.py` 的检查逻辑、白名单口径与输出格式。
- 不清理 `openspec/changes/archive/**` 里对 `dsh-plugins` 的历史提及（当时事实，改写即伪史）。
- 不动 profile、`$DSH_HOME`、`.gitignore`、`ruff.toml`、`tach.toml`（均未引用该目录，实证见 Impact）。

## Decisions

1. **整体删除目录，而不是「只删 arch-gate、留 patch.yml 空壳」。** `patch.yml` 的每一行都是写给唯一那个插件看的：`workspaceRoot: .` 的相对解析说明、`pathGlobs: backend/apps/**/*.py`、`passMarker: 零违规`、`--dump-config` 验证用法。留空壳等于留一个「以后再挂插件」的诱因，而这个诱因已被半年事实证伪（`2026-10-21` 之后就再没加过第二个插件）。真要做新插件时从零写一份 patch 条目成本相同，还不会继承过时注释。
2. **用 `git rm` 删除跟踪文件，`dist/` 随目录一并清掉。** 让 6 个跟踪文件以 `D` 进入暂存区、历史可追溯；`dsh-plugins/arch-gate/dist/`（`dist/index.js` 等构建产物）从未进 Git，直接删目录即可，不进提交。备选「只删工作区、提交时再 `git add -u`」会把删除动作与并发会话的改动混在同一批暂存里，放弃。
3. **不补 git hook / pre-commit 替代实时提醒。** 该插件唯一不可替代的能力是「把检查结果注入到模型当前回合的上下文」，hook 给不到；而 `python run.py check` 已是提交前置（`.agents/docs/github.md` 第 6 条），同一检查在提交前仍会跑。为一段 30 秒节流的重复提醒再维护一条 hook 链，收益不抵维护面。
4. **两处引用只改文案、不动代码。** `utils/gen_arch_stats.py` 里 UTF-8 reconfigure 的真实理由（stdout 被管道/重定向捕获时 GBK 抛 `UnicodeEncodeError`，退出码 1 与「发现违规」无法区分）与插件无关，去掉插件指涉即可，`hasattr` 守卫与 `reconfigure` 调用保持不变。

## 模块防火墙自检

- **跨 App import**：无。本变更不新增任何 import，删除的是仓库根的 TypeScript 插件。
- **service / runner / consumer / state_machine 跨 App 引用**：无。
- **写操作收敛到 `api.py`**：不涉及。本变更新增/修改零条 DB 语句，无迁移。
- **前端直连数据库 / 仪表盘写操作**：无。`dev_docs/project-viz/index.html` 只改一句目录列举文案，不涉及平台前端。
- **依赖方向**：无变化。`utils/gen_arch_stats.py` 仅删注释文字；`backend/`、`engines/`、`frontend/` 零改动。

## Risks / Trade-offs

- [有人仍按旧命令 `dsh web --patch dsh-plugins/patch.yml` 启动] → 文件不存在会**显式报错**，不是静默失效；且 README / AGENTS / 文档中该用法引用已归零，唯一出处是即将删除的插件自身 README。
- [以为 CI 等价覆盖，但 CI 只在 PR 时跑，日常写入不再有即时反馈] → 已知取舍：日常兜底靠 `python run.py check`（提交前置，同一检查），proposal 的 Impact 段已显式声明失去的是「实时提醒」。
- [仓库是共享工作区，`dsh-plugins/` 的删除与并发会话未提交改动混在同一个 `git status` 里被误提交] → 提交阶段逐文件 `git add` 本变更面（6 个 `D` + 2 个引用文件 + 4 个 openspec 文件），**禁止 `git add -A`**；提交前用 `git status --short` 复核暂存清单。
- [删除后想恢复] → 纯工作区/Git 变更，无数据迁移、无外部状态：`git revert` 对应提交即可完整恢复插件源码与 patch 层（`dist/` 可用 `cd dsh-plugins/arch-gate && npm run build` 重建）。

## 回退

`git revert <本变更提交>`：恢复 6 个跟踪文件与两处引用文案。插件复活需再跑一次 `npm run build` 生成 `dist/`（未跟踪，不在 Git 里），挂载命令回到 `dsh web --patch dsh-plugins/patch.yml`。
