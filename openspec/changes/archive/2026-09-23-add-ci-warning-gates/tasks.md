## 1. 基线确认

- [x] 1.1 本地运行 `cd frontend && npm run lint`：**69 个问题（0 error / 69 warning），退出码 0** —— 即 eslint 步骤在 CI 中为绿色，其价值在于暴露 69 条警告
- [x] 1.2 本地运行 `cd frontend && npm run typecheck`：**3 个 error**，全部集中在 `frontend/src/modules/case-manager/components/ProjectTree.vue` 的拖拽回调类型
- [x] 1.3 本地运行 `npx prettier --check "src/**/*.ts"`：**98 个 .ts 文件**需要重新格式化（占全部 167 个 .ts 文件的多数）
- [x] 1.4 本地运行 `python -m ruff check engines/`：`All checks passed!`；`ruff format --check engines/`：19 个文件已符合格式 —— 该范围当前无存量问题

## 2. 接入 CI（仅警告）

- [x] 2.1 新增独立 job `advisory-checks`（与拦截型 job 并行，避免被其失败跳过；理由见 design.md 决策 8），下述告警步骤全部落在该 job 内；每步失败时输出 `::warning::` 注解与输出末尾 40 行，步骤退出码保持 0
- [x] 2.2 新增 `ESLint (warning only)` 步骤（`npm run lint`）
- [x] 2.3 新增 `TypeScript check (warning only)` 步骤（`npm run typecheck`）
- [x] 2.4 新增 `Prettier check ts (warning only)` 覆盖 `src/**/*.ts`；既有 `Prettier check`（vue/js/css）的 glob 与拦截判定保持不变（理由见 design.md 决策 5）
- [x] 2.5 新增 `Ruff format check engines (warning only)` 与 `Ruff lint engines (warning only)` 覆盖 `engines/`；既有两条 ruff 步骤的作用域与拦截判定保持不变（理由见 design.md 决策 5）
- [x] 2.6 将 `eevog` 纳入 `push` 触发分支名单（`pull_request` 名单保持 `main` / `Kahoku` 不变）
- [x] 2.7 用 Python `yaml.safe_load` 校验 workflow：解析通过，6 个 job 与各步骤序列符合预期；`git diff -U0` 确认既有内容零删除（仅触发名单 1 行被替换）

## 3. 不回归确认

- [x] 3.1 `git diff -U0` 逐行核对：既有步骤的命令与判定**零改动**（唯一被替换的是触发名单 1 行）；新增内容为独立 job `advisory-checks`，删除行数为 0（注释行调整不计入判定改动）
- [x] 3.2 确认未改动各 job 的 `timeout-minutes`；`push` 名单仅按 2.6 新增 `eevog`，`pull_request` 名单保持 `main` / `Kahoku` 不变

## 4. 远端验证（触发已证实；执行受阻，改由本地门禁验证）

- [x] 4.1 提交并推送 `eevog`，确认 workflow 因该分支的推送被触发：**run #16（sha 099c5d10）已创建**，该分支此前 CI 运行次数为 0，触发名单改动生效
- [x] 4.2 **改由本地门禁验证**：GitHub Actions 侧 6 个 job 全部 `steps=0`、`runner=''`（账号付款失败导致作业未分配到运行器，run #13–#15 同样如此），"在运行记录中确认步骤已执行"这一手段不可用。改用变更 `2026-09-23-add-local-gate-runner` 的本地门禁 `python run.py check` 验证同一批检查确实会执行并产出结论：ruff（`engines/`）×2 PASS · eslint PASS · vue-tsc WARN · prettier（`.ts`）WARN
- [x] 4.3 **结论与基线一致**：上述 5 道检查的结论与第 1 组基线完全吻合，已作为后续「转拦截」的输入记录在本地门禁变更的基线表中
- [x] 4.4 **改由本地门禁验证**：本地实跑 20 项检查，既有拦截型检查（Django 检查 · ruff 平台范围 · 前端测试 · 前端构建 · prettier vue/js/css · 凭据扫描 · 模块边界 · Vue 体积 · 假数据）的判定口径与 CI 原文一致，新增的告警项不参与退出码

> **挂账（非本变更未完成项）**：CI 侧的**实际执行**验证仍无法完成——账号付款问题未解决前，作业不会被分配到运行器。本变更的职责（把 5 道检查接入 workflow、并让 `eevog` 的推送能触发）已完成且已验证；**CI 运行时能否真正跑起来属账号侧运维问题**，账号恢复后推送一次即可在运行记录中确认，无需再改本变更的任何代码。


## 5. 收尾

- [x] 5.1 更新 `AGENTS.md` 的「代码规范」一节：只保留**可机械验证**的内容——格式类要求以工具配置为准 · 语言与边界细节下沉到各层 · 已知盲区登记；删除「人工遵守、工具查不了」的跨语言原则清单（按要求，无法验证与查收的规则不入规范）

---

## 基线记录（2026-09-23 本地实测，供后续「转拦截」决策）

| 检查 | 范围 | 存量问题 | 步骤预期状态 |
| --- | --- | --- | --- |
| ruff check | `engines/` | 0 | 绿色 |
| ruff format --check | `engines/` | 0（19 文件已合规） | 绿色 |
| prettier --check | `src/**/*.ts` | 98 个文件需重新格式化 | 触发警告 |
| eslint | `frontend/src/` | 69 个 warning、0 error（退出码 0） | 绿色（警告仅记录在日志） |
| vue-tsc | `frontend/src/` | 3 个 error，均在 `ProjectTree.vue` | 触发警告 |

注：eslint 当前不拦截且退出码为 0，因此其 CI 步骤不会产生 `::warning::` 注解；警告明细只出现在日志中。若后续希望警告进入 PR 注解区，需在 `frontend/package.json` 的 `lint` 脚本上加 `--max-warnings 0`——属于后续独立变更。
