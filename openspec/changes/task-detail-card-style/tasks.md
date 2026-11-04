## 1. 步骤卡（CaseStepList）

- [x] 1.1 `CaseStepList.vue`：步骤行改为卡片，行首加 `.flow-step__status` 状态方块（`✓ / ✗ / △ / ○`，按 `outcome` 取类），行尾在结果徽标左侧加 `.flow-step__duration`；保留 `aria-expanded` / `aria-controls`。验证：`npx vitest run tests/task-list` 通过，DOM 中每个步骤同时有方块与文字标签。**验证结果**：方块类为 `is-pass / is-fail / is-pending / is-idle`，与徽标 `is-*` 同源；14 条步骤用例通过。
- [x] 1.2 `CaseStepList.style.css`：步骤卡白底 + 1px `ink 10%` 描边 + `--app-radius-sm` + 8px 间距；方块 28px / 圆角 8px / 状态四色；结果标签改软底胶囊（绿/红/黄/灰，无描边）；耗时 chip 天蓝填充 + 1px 描边 + `tabular-nums`；展开体改浅底内嵌，虚线全部改 1px 实线。验证：`npm run lint:styles` 不新增违规；`npm run build` 通过。**验证结果**：lint 输出中无 `CaseStepList` 条目（存量 50 处不变）；`build:check` 23.5s 通过。

## 2. 过程卡（RoundProcess）

- [x] 2.1 `RoundProcess.vue` / `.style.css`：过程卡改白底 1px + 左侧 3px 角色色条；块头耗时沿用 `.flow-proc__duration` 但改为天蓝 chip；交付/结论块改浅底实线；时间线分隔改 1px。验证：`npx vitest run tests/task-list` 通过，验收子块仍显示 `✅/❌`。**验证结果**：14:00 前后两轮全绿；`✅/❌` 断言未改动、仍通过。

## 3. 页面容器（TaskDetailPage）

- [x] 3.1 `TaskDetailPage.style.css` / `.vue`：用例卡、摘要四格去虚线硬投影，改白卡 1px；用例头保留「用例耗时 + 结果标签」；用例折叠标记与间距对齐卡片风。验证：页面上不再出现 `dashed`，`npm run build` 通过。**验证结果**：页面样式里已无 `dashed`；用例耗时改天蓝 chip + 等宽数字；`build:check` 通过。

## 4. 测试与门禁

- [x] 4.1 `tests/task-list/p0/task-detail-round-title.spec.ts`：补断言——步骤行有 `.flow-step__status` 且图标按结果映射；结果标签文本为 PASS/FAIL；有耗时时渲染 `.flow-step__duration`，无耗时不渲染。验证：`npx vitest run tests/task-list` 全绿。**验证结果**：新增 3 条（✓/✗/○ 映射、`3m03s` 与无耗时两种），该文件 11 → 14 条；整套 18 文件 137 passed。
- [ ] 4.2 门禁：`cd frontend && npx vitest run tests/task-list && npx vue-tsc --noEmit && npm run build:check` 全部通过（`lint:styles` 只允许既有存量为红）。验证：命令输出全绿。**当前状态**：vitest 137 passed、`vue-tsc` 0、`build:check` 通过；`lint:styles` 仍是改动前就存在的 50 处跨边界借用（本次三个文件 0 新增）。
- [ ] 4.3 页面人工验收：打开任务详情，确认步骤为卡片、结果方块与标签一致、耗时天蓝、全页无虚线。验证：用户目视确认。
