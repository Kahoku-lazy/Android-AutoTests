## 1. 共享层令牌与皮肤

- [x] 1.1 `tokens.css` 新增 `--comp-ac-card-pin-shadow: var(--color-ink-05-a18)`（`:root` 共享组件档，带原因注释）；验证：`lint:styles` 退出码 0，声明值为 `var()` 引用
- [x] 1.2 `workbench-theme.css` 的 `.wb-shell, .workflow-workbench` 块改用 `var(--app-font)` / `var(--ink)` 并补原因注释；验证：Chromium 实测 `.wb-shell` 的 `font-family` 解析为 `"Cascadia Mono"…`、`color` 为 `rgb(30,30,36)`
- [x] 1.3 `workbench-theme.css` 的 `.ac-card__pin` 阴影改用 `var(--comp-ac-card-pin-shadow)`；验证：全仓检索 `--ac-pin-shadow` 命中数为 0

## 2. 清理归零与重复的模块令牌

- [x] 2.1 `workflow/tokens.css` 删除 `--ac-font` / `--ac-ink` / `--ac-pin-shadow`；验证：三者声明与消费命中数为 0（残留的 `--ac-ink-muted` / `--ac-ink-faint` 是另一组令牌，属变更 14 范围；`workbench-theme.css` 的 1 处命中是本次修复的说明注释，有意保留）
- [x] 2.2 `workflow/tokens.css` 删除重复的 `--ac-accent`；验证：该文件内 `--ac-accent` 仅剩 1 条，值为 `var(--c-workflow)`（工作流天蓝，与模块色登记一致）

## 3. workflow 页根与页内按钮

- [x] 3.1 `workflow/index.vue:381` 页根改为 `doc-page doc-page--fixed wb-shell workflow-workbench`；验证：全仓 21 个页面根**全部**同时含 `doc-page` 与 `wb-shell`（或 `workflow-workbench`），无一遗漏
- [x] 3.2 删除 `.workflow-workbench` 上的 `height: 100%` 与 `overflow: hidden` 并写明理由，保留 `display:flex` / `flex-direction:column` / `min-height:0` / `background:transparent`；验证：`vite build` 通过，且已核实 `App.vue` 的 `:deep(.doc-page)` 编译为 (0,2,0) 高于 `.workflow-workbench` 的 (0,1,0)（两条原声明确为失效声明）
- [x] 3.3 页内对话框两个 `el-button` 补 `wb-btn`；验证：类覆盖交叉核对中 `.wb-btn` 命中数为 2（即本次有意新增），无其他意外命中

## 4. 门禁与验收

- [x] 4.1 `npm run lint:styles` 退出码 0；验证：批 1/2/3 全绿，"场景名/模块名别名"仍为 **48 条**、"消费位置裸色字面量"仍为 **33 处**（均未上升）
- [x] 4.2 `npx vite build --mode development` 通过（`built in 41.58s`，退出码 0）；验证：既有 `tests/dashboard/**` / `store.ts` / `ProjectTree.vue` 无关报错未新增（本变更未触碰任何 `.ts`）
- [x] 4.3 Chromium 断言（真实 CSS + 复刻 DOM，共 **9 项全 PASS**）：**缺陷复现** —— 在仅带 `.wb-shell` 的作用域下，旧规则 `box-shadow: 1px 2px 0 0 var(--ac-pin-shadow)` 计算为 `none`（因为模块令牌未声明）；改后 `.ac-card__pin` 计算为 `rgba(0,0,0,0.18) 1px 2px 0px 0px`，且与 `.workflow-workbench` 作用域下**完全一致**；`.workflow-workbench .ac-card` 仍取模块色 `rgb(137,207,240)`（`--c-workflow`）。**限制**：契约级验证，未加载真实运行的应用与数据
- [x] 4.4 交叉核对：`workflow/index.vue` 模板 17 个 class 与 `.wb-shell` 作用域共享皮肤选择器求交集，仅命中 `.wb-btn`（本次新增）、`.wb-shell` 与 `.workflow-workbench`（根类自身）→ 无未预期的样式命中
- [x] 4.5 `git diff --name-only` 本变更部分为 4 个文件：`modules/workflow/index.vue`、`modules/workflow/tokens.css`、`shared/styles/workbench-theme.css`、`shared/styles/tokens.css`，与 `proposal.md` 的 Impact 段一致；工作区其余改动属变更 1–4 与其他在飞工作，未触碰