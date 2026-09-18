## Why

`frontend/AGENTS.md` 的两个「代码范围」表把**文件行数/行区间**当成定位手段：`全文 16 行` · `全文 37 行` · `**33–55 行**（全文约 310 行）` · `**18 行起**（全文 428 行）` · `全文 71 行` · `302 行` · `~520 行` · `~55 行` · `116 行` · `75 行`。

这类数字**不提供导航价值**（没人靠「全文 302 行」去读文件），却会随每次编辑失效：本轮 P3 把 `tokens.css` 从 428 行降到 300 行、`style.css` 从约 310 降到 230，一次性让其中四处变成假信息；L1 §③ 的 `tokens.css:335` / `tokens.css:334` 是同一类脆断言（已因 P3 前移到 `:213` / `:212`）。

同一文件里还有一批**同类但不同性质**的数字，本变更不动（口径见 design）：指向行为的位置引用（`AppSidebar.vue:118-133`、`main.ts:27`）与规则阈值（`超过 500 行需拆分`）—— 前者帮定位、后者是规则，都不属「规模描述噪声」。

## What Changes

- `frontend/AGENTS.md` L0 §② 表：4 行的「位置」列改为**稳定描述**（`唯一 HTML 外壳` · `入口脚本（无组件）` · `顶部全局段（其后为组件类）` · `开头 :root 块（末尾另有全局工具类）`）
- `frontend/AGENTS.md` L1 §② 表：7 行的「位置」列由行数改为 `整份` 及其性质（`整份（scoped 引入）` / `整份（纯常量）`）
- `frontend/AGENTS.md` L1 §③：`--side-w`（`tokens.css:213`）· `--app-topbar-h`（`tokens.css:212`）→ 去掉行号，改为「`tokens.css` 根级」
- **不改**：指向行为的位置引用与规则阈值
- **BREAKING**：无（纯文档，`frontend/AGENTS.md` 不参与构建）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 唯一改动文件：`frontend/AGENTS.md`
- 同批但独立的代码变更：`close-typography-spacing-debt`（字号/间距）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 文档：`frontend/AGENTS.md`（L0 §② 4 行 · L1 §② 7 行 · L1 §③ 1 行）
- 源码：**0 行改动**
- 验证：改动后 `frontend/AGENTS.md` 内不再有「文件规模」型行数（仅保留规则阈值「超过 500 行」与行为位置引用）；每个「位置」描述都不含数字
