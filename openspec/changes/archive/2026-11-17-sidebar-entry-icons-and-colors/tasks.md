## 1. 图标

- [x] 1.1 `frontend/src/shared/icons/lucide-registry.ts`：自绘 `UsersAdmin`（一大一小两个人头 + 各自后肩）与 `ModelChip`（芯片本体 + 裸片 + 八根引脚），按 lucide 的 `IconNode` 形状书写（24 网格、线宽 2、圆头圆角），并登记进 `lucideIconSubset`。验证：`npx vue-tsc --noEmit` 通过；`temps/fold-check/shot-sidebar-icons.png` 里两个方块都有图案。
- [x] 1.2 `frontend/src/shared/components/sidebarNavConfig.ts`：运营两项的图标名改为 `users-admin` / `model-chip`（`data-lucide` 名与子集键按 PascalCase 对应）。验证：`npx vitest run tests/shared/p0/sidebarNavConfig.spec.ts` 的「图标都在子集里登记」用例通过。

## 2. 配色

- [x] 2.1 `frontend/src/shared/styles/tokens.css`：模块色别名段新增 `--c-account`（引用 `--color-blue-68-s64`）与 `--c-task`（引用 `--color-purple-56`），**不新增** `--color-*` 原子。验证：`npm run lint:styles` 的「批 2 调色板」一项通过（初版新增 `--color-lime-62` 被 G8 拦下，已改为复用）。
- [x] 2.2 同文件 `sidebarNavConfig.ts` 的 `MOD_COLORS`：串口日志 → `--c-workflow`；运营三项 → `--c-account` / `--c-element` / `--c-ops`；任务清单 → `--c-task`。验证：同分组内两两不同，见 `temps/fold-check/shot-sidebar-icons.png` 的「改后」一列。

## 3. 测试

- [x] 3.1 `frontend/tests/shared/p0/sidebarNavConfig.spec.ts`：新增「每个导航图标都在 `lucideIconSubset` 里登记」用例（漏登记即空方块，这次就是被它挡住的那类回归）。验证：该文件 9 passed。
- [x] 3.2 同文件：新增「数据组两项不同色」「运营组三项互相不同色」「任务清单与 AI 助手不同色」「每个导航入口都有模块色」四个用例；旧的 `/tasks === var(--c-ai)` 断言同步改为 `--c-task`。验证：同命令通过。

## 4. 文档登记

- [x] 4.1 `.agents/skills/doodle-craft/SKILL.md` 与 `references/tokens.md`：彩笔令牌表 9 → 11，登记 `--c-account` / `--c-task` 的色值与消费方，写明「入口级色、复用原子、同分组不同色」的口径。验证：两处表格与 `tokens.css` 声明一致。

## 5. 门禁

- [x] 5.1 `npx prettier --check` / `npx eslint` / `npx vue-tsc --noEmit` 对改动的三个前端文件通过。验证：三条命令退出码 0。
- [x] 5.2 `npm run lint:styles` 的批 2 通过；批 4 仍报 `AppSidebar.style.css:209` 的未登记圆角 `8px`——该行在 HEAD 上就是这样，本次未触碰，属既有欠账。
- [ ] 5.3 `python run.py check` 全绿：仍被仓库既有 12 项失败挡住（与本次无关，明细见 `report-fold-sections` 归档的任务 4.3）。
