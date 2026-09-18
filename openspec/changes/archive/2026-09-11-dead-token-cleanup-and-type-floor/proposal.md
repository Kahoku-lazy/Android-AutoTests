## Why

设计系统有两个具体缺陷让"令牌是唯一真相源"名不副实：① `tokens.css` 307 个令牌中 **149 个零使用**，其中 `--app-glass-*`(5) / `--doodle-font-*`(4) / `--app-sidebar-*`(4) 三个家族已被明确标注 legacy/@deprecated 且实测全仓库 0 引用；② 字号门禁（最小 12px）有 **6 处**硬编码违规，但**没有任何可执行检查**——规则只存在于 tokens.css 注释与 skill checklist 里。批 1 只做"低风险、无可见行为变化"的部分（批 2/3 另行决策）。

## What Changes

- 删除 13 个零使用令牌（tokens.css **307 → 294**）：`--app-glass` / `--app-glass-blur` / `--app-glass-border` / `--app-glass-card` / `--app-glass-heavy`；`--doodle-font-hand` / `--doodle-font-mono` / `--doodle-font-title` / `--doodle-font-ui`；`--app-sidebar-active` / `--app-sidebar-bg` / `--app-sidebar-collapsed` / `--app-sidebar-w`
- 同步 tokens.css 文件头的 @deprecated 清单（移除已删的 `--app-glass-*` 提及）
- **6 处**字号 < 12px 归 `var(--app-size-xs)`（12px）：FilterTabs 11、CaseFileSheet 11/10、ProjectTree 11、ToolboxPanel 10、PageElementsPanel 9
- 新增可执行门禁：`frontend/tests/check-style-gates.mjs`（字号下限 12px；默认告警 exit 0，`--strict` 违规 exit 1）+ npm script `lint:styles`
- **无 BREAKING**：13 个令牌 0 引用；字号变更仅影响 6 个小标签/徽标的像素尺寸

## 关联文档

- 无 PRD/ARCH 关联：设计系统清理（批 1/3），依据 = tokens.css 注释口径 + `vue-frontend-check` checklist 第 1 条
- 既有偏差继续登记（本批不改）：tokens.css 头注"现行体系（frontend/AGENTS.md §2 口径）"仍指向已不存在的 §2

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯令牌/字号清理 + 门禁新增，无需求级行为变化：`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 修改 6 个源文件 + `frontend/package.json`；新增 1 个门禁脚本
- 令牌 307 → 294；`font-size < 12px` 6 → **0**
- 验证：门禁脚本（默认与 `--strict` 均通过）· `vue-tsc` 35 条既有错误不变且与本次改动无关 · 13 个令牌名全仓库 **0 残留**
- 未纳入本批（批 2/3 登记）：滚动策略收敛（三层滚动 + 39 处手写容器）· 间距/圆角令牌化（667/174 处字面量，**非等值项需设计决策**）· 其余 136 个零使用令牌（模块专属 `--ai-*`/`--case-*`/`--app-stat-*` 建议**下沉**而非删；EP 映射 `--el-*` 15 个待单独决策）· 外壳作用域（`.wb-shell` 仅 8 处）
