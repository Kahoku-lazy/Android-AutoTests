## Why

L2/L3 两份现状复盘报告（`dev_docs/05-开发与测试/设计方案与报告/报告-前端区域层级与{L2,L3}现状复盘.html`）与 `frontend/AGENTS.md` 中，有一批**已被后续变更推翻的现状描述与数值**，继续留着会误导接手者：

| # | 位置 | 现状描述 | 真实情况（已实测） |
|---|------|----------|--------------------|
| 1 | L3 §五 · 步骤状态 | 「② 统一容器口径 ⬜ 待开 · ③ 收敛块语言 ⬜ 待开」 | ②③ **均已落地并归档**（`unify-l3-container` · `converge-l3-block-language` · `fix-l3-container-residual`） |
| 2 | L3 §五 | 「全局 `.doc-body` 水平内边距 32px ≠ 页头 24px」 | 已由 `unify-l3-container` 对齐为 24px |
| 3 | L3 §五 / L2 §五 | 「6 处模块点阵与 L0 口径冲突」 | 6 处已于 `unify-l3-container` 全部删除 |
| 4 | L3 §五 | 「`--app-paper-dot` 消费方…（待实施后归零）」 | P3 批次① 已退役该令牌，全仓 0 命中 |
| 5 | L3 §五 | 「legacy 令牌 `--doodle-bg` **7 处**」 | 实测 **5 处** |
| 6 | L3 §五 / L2 §五 | 「一处裸 px 间距 `gap:14px`」 | 实测 **6 处**（5 个文件），仍挂起 |
| 7 | L3 §五 / L2 §五 | 「A/C 类 scoped `.doc-page { height:100% }` 是死声明（待清）」 | `remove-dead-doc-page-declarations` 已删 5 处（保留 2 处登记例外） |
| 8 | L3 §五 | 「裸 `.doc-body` 覆写 5 处」 | `fix-l3-container-residual` 已收敛为模块 modifier 限定 |
| 9 | L3 §五 | 「画布页 `.wb-body` 待步骤② 登记」 | 已登记进 `frontend-l3-container` / `frontend-l2-page-region` 两份 spec |
| 10 | L3 §七 / L2 footer | 变更记录只到步骤 ① / 同步范围只写 `remove-frontend-dead-code` | 需补 ②③ + P3 三批 + 残留死代码清理 |
| 11 | `frontend/AGENTS.md` L0 §② | `tokens.css`（全文 **428 行**）· `style.css`（全文约 **310 行**）· `main.ts` 全文 **37 行** | 实测 **300** / **230** / **34** 行（tokens.css 缩小就是 P3 三批的结果） |
| 12 | `frontend/AGENTS.md` L1 §③ | `--side-w`（`tokens.css:335`）· `--app-topbar-h`（`tokens.css:334`） | 行号已随 P3 删除前移，实测 **213** / **212** |

## What Changes

- `报告-前端区域层级与L3现状复盘.html`：§五 9 条风险/待办改写为当前状态（含 `--doodle-bg` 5 处、`gap:14px` 6 处、死声明/点阵/裸覆写/画布例外已完成）；§六 结论与三步状态改「②③ 已落地」；§七 变更记录补 ②③、P3 三批、残留清理共 6 条；footer 同步范围更新
- `报告-前端区域层级与L2现状复盘.html`：§五 4 条改写（死声明已删 · 点阵已删 · `gap:14px` 6 处 · 画布例外已登记）；§六「下一层工作」改写；footer 同步范围更新
- `frontend/AGENTS.md`：L0 §② 三处行数改正（`main.ts` 34 · `style.css` 230 · `tokens.css` 300）；L1 §③ 两处令牌行号改正（`--side-w` 213 · `--app-topbar-h` 212）
- **BREAKING**：无（纯文档同步，不动任何源码）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 被同步的文档本身即本变更的全部影响面（2 份 HTML 报告 + `frontend/AGENTS.md`）
- 事实来源：`openspec/changes/archive/` 下 6 个已归档变更（`unify-l3-container` · `converge-l3-block-language` · `fix-l3-container-residual` · `remove-dead-doc-page-declarations` · `remove-dead-animation-exports` · P3 三批 · `cleanup-residual-dead-code`）与本地实测计数
- 无需求/架构/接口文档受影响（`dev_docs/02-PRD需求`、`03-设计与架构`、`05-.../接口文档` 对本批内容 0 提及）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 文档：2 份 HTML 现状复盘报告（§五/§六/§七/footer）+ `frontend/AGENTS.md`（2 处）
- 源码：**0 行改动**
- 版本控制提示（实测发现）：两份 HTML 报告被 `.gitignore:121` 的 `dev_docs/**/*.html` 排除（该目录 8 份 HTML 全部未跟踪，属仓库既有约定）→ 它们不产生 `git diff`，回滚只能手工回退；`frontend/AGENTS.md` 是本变更唯一进入版本控制的文件
- 验证：改动后逐条复核文档中的每个数值/状态均能对应到归档变更或本地实测；`git status --porcelain -- frontend/AGENTS.md` 与 `git diff --numstat` 确认改动范围内无源码文件
