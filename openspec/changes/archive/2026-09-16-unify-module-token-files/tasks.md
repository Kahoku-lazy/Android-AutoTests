## 1. element-locator 令牌文件化

- [x] 1.1 新建 `modules/element-locator/tokens.css`，在 `.locator-workbench` 下声明 `--locator-header-icon-end`；验证：`lint:styles` 批 2/批 3 通过（含 G7 模块前缀声明不得持字面量）
- [x] 1.2 `main.ts` 增加 `import './modules/element-locator/tokens.css'`；验证：`vite build` 通过（34.44s）
- [x] 1.3 为 3 个页根补 `locator-workbench` 类；验证：全仓 `locator-workbench` 命中 **5** 处 = tokens.css 注释 1 + 选择器 1 + 3 个页根
- [x] 1.4 删除 3 处内联声明块（含失真的"tokens.css 未登记 #c4b5fd"注释）；验证：`--locator-header-icon-end` 全仓声明数 = **1**（tokens.css:8）

## 2. case-manager 令牌上收

- [x] 2.1 `case-manager/tokens.css` 新增 `--case-icon-accent: var(--color-teal-67)`；验证：该文件含 3 条模块令牌
- [x] 2.2 删除 `CaseFileSheet.vue` / `ProjectList.vue` / `ProjectWorkspace.vue` 中重复声明；验证：`--case-icon-accent` 全仓声明数 = **1**（tokens.css:10）
- [x] 2.3 保留元素局部登记：`--case-menu-shadow` 仍在 2 处浮层元素自身（Teleport 到 body 后模块根不再是祖先，必须留在元素上）、`--case-sheet-grid` 仍在表元素 `.case-sheet__table`；验证：计数分别为 2 / 1，未改动

## 3. 门禁与验收

- [x] 3.1 `npm run lint:styles` 退出码 0；验证：批 1/2/3 全绿
- [x] 3.2 `npx vite build --mode development` 通过（`built in 34.44s`，退出码 0）；验证：既有无关报错未新增（本变更未触碰 `.ts`）
- [x] 3.3 编码安全：全部改动由 `edit` 工具完成（无脚本批量改写）；验证：乱码扫描命中 **0**
- [x] 3.4 Chromium 断言（真实 `tokens.css` + 两个模块 `tokens.css` + 复刻 DOM）：`.locator-workbench` 作用域下 `--locator-header-icon-end` 解析为 `#c7b6f8`（indigo-84）、`.case-workbench` 作用域下 `--case-icon-accent` 解析为 `#6ee7d8`（teal-67）、既有的 `--case-border` 仍解析为 `rgba(162,209,254,0.3)` 未被破坏；**3 项断言全 PASS**。**限制**：契约级验证，未加载真实运行的应用与数据
- [x] 3.5 令牌落点复核：两个模块的**模块级**令牌声明全部落在各自 tokens.css（各 1 处）；元素局部登记项（`--case-sheet-*` / `--case-menu-shadow`）按设计保留在原处
- [x] 3.6 `git diff --name-only` 清单与 `proposal.md` 的 Impact 段一致（新建 1 + `main.ts` + element-locator 3 页 + case-manager tokens.css 与 3 页）

## 4. 本轮新发现（登记为后续输入）

- [x] 4.1 同类碎片化比原报告更广：`report-generator`（5 条 `--rg-*`）与 `dashboard`（5 条 `--ch-*`）**都没有 tokens.css**，且页根类不统一（`report-generator` 4 个页根各不相同）。本变更只处理计划内的 element-locator 与 case-manager；已把两者登记进变更 14 的输入（含"页根统一"这一前提工作）
- [x] 4.2 `--case-*` 家族的**色相**问题（值取自 blue 族而模块色 `--c-case` 是 teal）**未擅自改动** —— 改色会改变用例表表头与分隔线观感，属设计选择，已记入 `design.md` 的 Open Questions 与看板备注