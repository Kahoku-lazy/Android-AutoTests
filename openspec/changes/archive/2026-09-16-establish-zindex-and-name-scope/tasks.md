## 1. 层叠令牌与悬空引用

- [x] 1.1 `tokens.css` 登记 7 档层叠令牌（与现状逐一相同），并在注释中登记未纳入档位的 5 个单例值（`0/3/5/20/100`）；验证：`lint:styles` 批 2/3 通过
- [x] 1.2 `case-manager/tokens.css` 声明 `--case-z-context: var(--z-overlay)`；验证：Chromium 实测原悬空引用处计算 `z-index` 由 `auto` 变为 **80**
- [x] 1.3 全仓把与令牌精确同值的 `z-index` 字面量替换为令牌；验证：替换 **21** 处（`--z-base` 6、`--z-raised` 6、`--z-header` 3、`--z-popup` 3、`--z-overlay` 1、`--z-modal-backdrop` 1、`--z-modal` 1），剩余字面量恰为 5 个已登记单例

## 2. 命名作用域

- [x] 2.1 element-locator `ProjectList.vue` 的 `project-list-page` → `locator-project-list`（模板 + CSS）；验证：精确词边界检索下该旧名仅出现在 case-manager
- [x] 2.2 element-locator `ProjectWorkspace.vue` 的 `project-workspace` → `locator-project-workspace`；验证：同上
- [x] 2.3 case-manager `ProjectTree.vue` 的 `.ex-btn` 对齐到 `LocatorTree.vue` 的规格（底色 `--app-bg-card` → `--paper`、圆角 `--app-radius-md` → `--app-radius-sm`、内边距 `7px 12px` → `6px 12px`）；验证：两者圆角与底色同源、内边距一致

## 3. 门禁与验收

- [x] 3.1 精确词边界检索确认无跨模块同名页根类：`project-list-page` 与 `project-workspace` **各自只出现在 case-manager**；验证：输出检索结果（注意：初次用子串检索出现 4 处假阳性 —— `locator-project-workspace` 含 `project-workspace` 子串，已改用 `(?<![\w-])…(?![\w-])` 边界）
- [x] 3.2 `npm run lint:styles` 退出码 0；验证：批 1/2/3 全绿
- [x] 3.3 `npx vite build --mode development` 通过（`built in 33.62s`，退出码 0）
- [x] 3.4 编码安全：改动由 `edit` 工具与 UTF-8 安全 ASCII 脚本完成；验证：乱码扫描 **0**
- [x] 3.5 Chromium 断言（**3 项全 PASS**）：① `case-manager` 作用域下 `z-index: var(--case-z-context)` 计算为 **80**（修复前为 `auto`）；② element-locator 改名后的页根类下 `.doc-body` 仍取到模块内边距 **24px**（改名未打断样式）；③ 7 个层叠令牌解析值 **逐一等于**原字面量（1/2/10/60/80/9990/9991），即**零视觉层叠变化**。**限制**：契约级验证，未加载真实运行的应用与数据
- [x] 3.6 `git diff --name-only` 清单与 `proposal.md` 的 Impact 段一致（`tokens.css` + 约 20 个含 z-index 的文件 + case-manager tokens.css/ProjectTree.vue + element-locator 两个页面）