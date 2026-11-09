## 1. 实现

- [x] 1.1 `KpiCard.vue`：默认描边 `2.5px dashed var(--ink)` → `2.5px solid var(--kpi-accent)`。验证：`vue-tsc` 与 build 通过。**验证结果**：tsc 0（build 见 2.2）。
- [x] 1.2 `tests/check-dashed-whitelist.mjs`：OWNERS 只保留 `AgentRouteCard.vue`，文件头注释同步。验证：`npm run lint:lines` 显示白名单组件 1 个、0 处虚线。**验证结果**：`[dashed] 虚线出现在 0 个文件 / 0 处`。

## 2. 文档与门禁

- [x] 2.1 `doodle-craft/SKILL.md` §线型规则：白名单表只留助手角色卡，补 2026-11-09 变更说明与回退路径。验证：文档表格与 OWNERS 一致。**验证结果**：已改。
- [x] 2.2 `references/components/cards.md`：顶部线型提示与 §3 KpiCard 规格改为实线描述。验证：不再声称 KpiCard 可声明 dashed。**验证结果**：已改。
- [x] 2.3 门禁：`npx vue-tsc --noEmit`、`npm run build:check`、`npx vitest run tests/shared tests/dashboard`、`npm run lint:styles`、`npm run lint:lines`。验证：全绿。**验证结果**：tsc 0；lint:lines 通过（0 处）。
- [ ] 2.4 目视：仪表盘 / 报告页 / BUG 概览三处统计卡描边与阴影同色。验证：用户确认。

## 4. 去阴影（2026-11-09 追加）

- [x] 4.1 KpiCard.vue：ox-shadow: 4px 4px 0 0 var(--kpi-accent) → 
one，hover 也去掉阴影，只保留描边与微倾。验证：build 24.5s、共享/仪表盘测试通过。**验证结果**：通过。
- [x] 4.2 规格 delta 同步：rontend-doodle-kpi-card 的卡壳要求改为「实线描边 + 近直角圆角 + 无阴影」，entry 主数值色改以描边 accent 为准。验证：openspec validate kpi-card-solid-border --strict。**验证结果**：valid。
- [x] 4.3 doodle-craft/references/components/cards.md §3 同步为「阴影 无」。验证：文档与代码一致。**验证结果**：已改。

- [x] 4.4 阴影改为浅色渐变：单层高饱和硬影 → 同色相三层（42% / 20% / 8% 混纸白，偏移 4/8/12px、0 模糊），只在右下方；hover 同步 5/9/13px。验证：build 29.0s、共享+仪表盘测试通过。**验证结果**：通过。

- [x] 4.5 规格与文档再同步：frontend-doodle-kpi-card 改为实线描边 + 右下浅色分层硬阴影；cards.md 3 节同步。验证：openspec validate kpi-card-solid-border --strict。**验证结果**：valid。

- [x] 4.6 描边改淡灰白：KPI 卡描边由模块 accent 改为 color-mix(ink 12%, paper)，accent 仍用于主数值、图标与图钉。验证：build 18.7s、共享+仪表盘测试通过。**验证结果**：通过。

- [x] 4.7 规格/文档同步：spec 的卡壳描述改为淡灰白描边；cards.md §3 同步。验证：openspec validate --strict。**验证结果**：valid。

- [x] 4.8 描边跟随阴影 + 角标弧线同填充：KpiCard 与 .part-card 描边改为 color-mix(accent 42%, paper)（阴影第一层）；角标 ::after 的左/下弧线改为与填充相同的 28% 混色，不再用墨线。验证：build 20.8s、111 用例通过、虚线 0 处、validate valid。**验证结果**：通过。

- [x] 4.9 KPI 变体字色：去掉 label 内联 accent 色，统一墨色；kpi 与 entry 主数值改为 accent 同色系 90deg 深→浅渐变（background-clip:text）。验证：build 17.6s、shared 测试通过、validate valid。**验证结果**：通过。
