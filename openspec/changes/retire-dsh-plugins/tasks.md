## 1. 目录退役

- [x] 1.1 `git rm` 6 个跟踪文件：`dsh-plugins/patch.yml`、`dsh-plugins/arch-gate/README.md`、`dsh-plugins/arch-gate/package.json`、`dsh-plugins/arch-gate/tsconfig.json`、`dsh-plugins/arch-gate/src/index.ts`、`dsh-plugins/arch-gate/src/node-stubs.d.ts`（PowerShell 下逐条写路径，不依赖 glob 展开）。验证：`git status --short -- dsh-plugins` 恰好 6 行且全为 `D`，无 `??`。**实测**：首次在 workspace-write 下被 NTFS 拒绝（`index.lock: Permission denied`；探针证明低完整性令牌无法写 `.git` 与 `dsh-plugins/` 下既有对象），改用完全权限后 `git rm -r --ignore-unmatch dsh-plugins` 一次成功，6 个文件全部落在暂存区。
- [x] 1.2 删除残留的未跟踪构建产物并移除空目录：`Remove-Item -Recurse -Force dsh-plugins`。验证：`Test-Path dsh-plugins` 为 `False`；`git status --short -- dsh-plugins` 仍只有上述 6 个 `D`（证明未跟踪的 `dist/` 没被带进暂存）。**实测**：删前仅剩 `arch-gate/dist/index.js` 与三个空目录；删除后 `Test-Path` 为 `False`，状态仍为 6 个 `D`，无 `??`。

## 2. 引用清理

- [x] 2.1 `utils/gen_arch_stats.py` 模块 docstring（第 28–32 行注释）：把「会让 CI 与 dsh-plugins/arch-gate（execFile 捕获 + passMarker "零违规"）误判失败」改成不点名插件的通用表述，保留「被管道/重定向捕获」这一真实因果，`reconfigure` 调用与 `hasattr` 守卫**不动**。验证：`Select-String -Path utils\gen_arch_stats.py -Pattern 'dsh-plugins|arch-gate|passMarker'` 命中 0；`python utils/gen_arch_stats.py --check-boundaries` 退出码 0 且 stdout 含「零违规」。**实测**：改为「…与『发现边界违规』的退出码无法区分，任何按退出码判定的调用方（CI 步骤、脚本门禁）都会误判为检查失败。」；全仓 grep 该文件命中 0；`--check-boundaries` 输出「✅ 模块边界检查通过 — 零违规」、退出码 0。
- [x] 2.2 `dev_docs/project-viz/index.html` 顶层目录说明删掉 `<code>dsh-plugins</code>（插件）、` 片段，保留 `dev_docs` / `temps` / `openspec` / `tools/platform-tools` 四项。验证：`Select-String -Path dev_docs\project-viz\index.html -Pattern 'dsh-plugins'` 命中 0；该 `<p>` 仍列举其余四项且无残留顿号。**实测**：该行现为「…`openspec`（规格文档）、`tools/platform-tools`（adb 二进制）都不属工程代码目录；目录列举与顿号完整。

## 3. 全仓归零与门禁

- [x] 3.1 全仓引用归零（排除依赖与历史归档）：对 `*.py,*.ts,*.js,*.mjs,*.vue,*.md,*.yml,*.yaml,*.json,*.toml,*.html` 递归搜索并跳过 `node_modules`、`.venv`、`.git`、`.agents/skills`、`openspec/changes/archive`，`dsh-plugins|arch-gate` 命中 0；再单独搜 `openspec/changes/archive`，命中只允许出现在历史变更产物里，逐条列出行号与「历史事实」判定。**实测**：全仓（ripgrep，跟随 .gitignore）共 59 处命中，全部落在两类：① `openspec/changes/retire-dsh-plugins/{proposal,design,tasks}.md`（本变更自身描述）；② `openspec/changes/archive/2026-09-14-fix-arch-gate-encoding`、`2026-10-21-backend-package-layout`、`2026-10-21-move-dev-tools-to-utils`（历史事实，按设计不改写）。`utils/`、`dev_docs/`、`backend/`、`engines/`、`frontend/`、CI 配置命中均为 0。
- [x] 3.2 本地门禁 `python run.py check` 退出码 0。若红项来自并发会话的既存改动（当前工作区有大量他人在改的文件），标注归属并单独举证本变更面（1 个注释文件 + 1 个文案文件 + 6 个删除文件）不落在红项检查范围内。**实测**：退出码 1，阻塞项 18/28 通过。红项全部归因于环境缓存权限与并发会话未提交改动，无一落在本变更面：
  - `ruff-*`（4 项）：首轮因 `.ruff_cache` 的 ACL 拒绝访问失败（`os error 5`），清缓存后实测剩余红项为 `backend/apps/task_list/task_runner.py`、`tests/engines/backend_bridge/unit/test_bound_team.py`、`utils/check_gates.py` 的格式与 `tests/engines/ae_harness/unit/test_{goal,team}_pipeline.py` 的 `I001`——全部在 `git status` 的他人改动集内。本变更文件单独实测：`ruff format --check utils/gen_arch_stats.py` → already formatted；`ruff check utils/gen_arch_stats.py` → All checks passed。
  - `prettier` / `vue-tsc` / `vitest` / `vite-build` / `openapi-schema` / `openapi-coverage`（6 项）：分别指向 `frontend/src/modules/knowledge-search/{ModulePanel,RetrievalSettingsCard}.vue`（未跟踪新文件）、`backend/apps/knowledge_search/**` 的接口基线漂移，以及 `frontend/node_modules/.vite-temp`、`frontend/vite.config.js.timestamp-*` 的 `EPERM`——同上，均为并发会话或环境缓存问题。
  - 与本变更相关的门禁项 `boundary`（模块边界检查）**PASS**；`business-asset`、`engines-agents-retirement`、`silent-except` 等亦 PASS。
- [x] 3.3 `openspec validate retire-dsh-plugins --strict` 通过（`skip_specs: true` 下不得报缺 delta）。**实测**：`Change 'retire-dsh-plugins' is valid`，`status` 显示 proposal/design/tasks 均 `done`、specs `skipped`。

## 4. 提交与 PR

- [x] 4.1 从 `Kahoku` 切出特性分支 `retire-dsh-plugins`（分支切换不改工作区文件，并发会话的未提交改动原样保留）。验证：`git rev-parse --abbrev-ref HEAD` 为 `retire-dsh-plugins`；`git status --short` 中并发会话条目与切换前逐条一致（数量与路径不变）。**实测**：`git switch -c retire-dsh-plugins` 后 HEAD 指向新分支，工作区未动；并发会话的改动条目一条未少，只有本变更的 12 个文件进入提交。
- [x] 4.2 逐文件暂存本变更面：6 个 `D` + `utils/gen_arch_stats.py` + `dev_docs/project-viz/index.html` + `openspec/changes/retire-dsh-plugins/{proposal.md,design.md,tasks.md,.openspec.yaml}`。**禁止 `git add -A`**。验证：`git diff --cached --name-status` 恰好 12 行（6 `D` + 2 `M` + 4 `A`），无其它路径。**实测**：暂存清单 12 行（`D`×6、`M`×2、`A`×4），`git diff --cached --numstat` 显示两个改动文件各为 1 行、2 行的最小 diff，无行尾噪声。
- [x] 4.3 提交 `chore(dsh-plugins): 退役从未加载的 arch-gate 写后边界插件`。验证：`git log -1 --stat` 的文件清单与 4.2 的暂存清单逐条一致。**实测**：提交 `5bf5173c`，`12 files changed, 126 insertions(+), 350 deletions(-)`，清单与 4.2 完全一致。
- [x] 4.4 推特性分支并开 PR：`git push origin retire-dsh-plugins`、`gh pr create --base Kahoku`，等 `ci-phase1.yml` 的 `python` 与 `frontend` 两个 job 全绿。验证：`gh pr checks` 两 job 均为 pass；失败则按日志修复后重推（不强推主干、不改写历史）。**实测**：本机 Clash 代理（`127.0.0.1:7897`）未启动导致首次推送失败，绕过代理（`git -c http.proxy= -c https.proxy= push`）推送成功；PR **#36** https://github.com/Kahoku-lazy/Android-AutoTests/pull/36 ；`gh pr checks 36` → `python pass 3m03s`、`frontend pass 1m43s`。**注**：本地 `run.py check` 的 10 个红项在 CI 上不复现，直接印证它们是并发会话未提交改动所致。
- [ ] 4.5 合并后归档：`openspec archive retire-dsh-plugins`，逐文件 `git add` 归档产物后提交 `docs(openspec): 归档 retire-dsh-plugins`。验证：`openspec list` 不再列出该 change；`openspec/changes/archive/<日期>-retire-dsh-plugins/` 含归档后的 4 个产物。（待 PR #36 合并后执行）
