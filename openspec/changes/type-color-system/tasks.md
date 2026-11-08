## 1. P0 令牌层

- [x] 1.1 `tokens.css`：新增 `--font-weight-regular/medium/semibold/bold/heavy`（400/500/600/700/800）与 `--line-height-tight/snug/normal/relaxed`（1.25/1.4/1.5/1.7），并提供 `--app-font-weight-*` / `--app-line-height-*` 别名。验证：`npm run lint:styles` 批 2 通过。**验证结果**：批 2 通过（颜色原子 83 个 / 上限 99）。行高最终取 1.25/1.4/1.5/1.7 —— 按现状 1.5（15 处）与 1.6（9 处）的众数选了漂移更小的组合。
- [x] 1.2 `tokens.css`：新增颜色原子 `--color-ink-42: #6b6b74`；`--app-text-primary/tertiary/disabled`、`--app-bg-canvas/muted`、`--app-border-subtle/strong`；`--app-text-secondary` 改指向 `--color-ink-42`（5.21:1）。验证：调色板门禁通过。**验证结果**：批 2 通过；原子 99 个（新增 ink-42，P2 再删 16 个）。
- [x] 1.3 `check-style-gates.mjs`：`PALETTE` 增加 `--color-ink-42`。验证：`npm run lint:styles` 批 2 通过。**验证结果**：通过，上限自动从 98 到 99。

## 2. P1 组件层

- [x] 2.1 字重令牌化：`font-weight: 400/500/600/700/800` → `var(--app-font-weight-*)`（含 `!important`）。验证：全仓 `font-weight: \d` 仅剩令牌声明。**验证结果**：282 处替换，字面量归零（700/800 含 `!important` 变体）。
- [x] 2.2 行高令牌化：`line-height: 1.2/1.35/1.4/1.45/1.5/1.6/1.7/1.65/1.8` → 最近档令牌；`1` 与 px 值保留。验证：`npm run lint:styles` 通过。**验证结果**：74 处替换；残留仅 `line-height: 1`（12 处，图标）与 16/18px 固定高（允许）。
- [x] 2.3 文字色语义化：`color: var(--ink)` → `var(--app-text-primary)`。验证：`vue-tsc` / build 通过。**验证结果**：195 处替换；`vue-tsc` 退出码 0，build 通过。
- [x] 2.4 边界线语义化：`border/outline` 里的 `var(--color-ink-79)` → `var(--app-border-subtle)`。验证：`npm run lint:styles` 与 build 通过。**验证结果**：3 处替换；其余边框已是 `color-mix`，无需替换。
- [x] 2.6 平台名称与页头标题：侧栏标识「自动化测试平台」→「智能化测试平台」：去掉 AI 方块图标；「智能化」三字取山景渐变（blue-27 → teal-38 → green-49 + 0.35px 描边），「测试平台」保持墨色；登录页 hero 与仪表盘副标题同步改名；页头标题 WorkbenchHeader 32px → 24px 并改手写体；页头副标题整体停用（.brand-sub 删除，prop 暂留兼容调用点）。验证：ue-tsc / build / 	ests/shared+	ests/dashboard 通过。**验证结果**：uild:check 27.7s、ue-tsc 0、108 测试通过；页标题 2xl → xl、--app-font-brand 400。
- [x] 2.5 侧边栏排版：平台标识改 `--app-font-brand`（20px / 400，登录页同款手写体）；导航项 14 → 16（行高 46）；分组标题 12 → 14 并去掉 `opacity: .45`、改 `--app-text-secondary`（2.81:1 → 5.21:1）。验证：`vue-tsc` / build / `lint:styles` 批 2 通过。**验证结果**：`build:check` 34.8s 通过；批 2 通过（批 3 仍 50 处既有）；`tests/shared` 11 文件 49 passed。底部用户区本来就是 16px，未改。

## 3. P2 收敛

- [x] 3.1 删除 16 个从未被引用的颜色原子。验证：`var(--color-*)` 无悬空引用（门禁 G4）。**验证结果**：原子 98 → 83，从未引用 0 个；G4 通过。
- [x] 3.2 字号字面量归零：`AgentRouteCard` 的 18/15/13px → 20/14/12 令牌；`EmptyState` 40px → `3xl`；`NotFound` 96px → 新增 `--app-size-4xl`。验证：全仓 `font-size: \d` 为 0。**验证结果**：374 处声明全部走令牌，字面量 8 → 0。

## 4. 门禁与验收

- [x] 4.1 前端门禁：`npm run lint:styles`（批 2/3/4）、`npm run lint:lines`、`npx vue-tsc --noEmit`、`npm run build:check` 通过。验证：命令输出。**验证结果**：批 2/4 通过；批 3 仍是既有 50 处跨边界借用（本次未新增）；`lint:lines` 0 处；`vue-tsc` 0；`build:check` 91s 通过。
- [x] 4.2 全量前端测试：`npx vitest run` 全绿。验证：退出码 0。**验证结果**：76 文件 463 passed，退出码 0。
- [ ] 4.3 页面目视：仪表盘、任务详情、助手看板、登录页看完一轮（文字层级、边框、对比度）。验证：用户确认。
