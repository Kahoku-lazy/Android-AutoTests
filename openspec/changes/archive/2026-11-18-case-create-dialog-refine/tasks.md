## 1. 动作键

- [x] 1.1 `ProjectList.vue` 的弹窗 `#footer` 由 `el-button` 换成共享 `DoodleBtn`（`paper` 取消 / `yellow` 创建），`creating` 期间 disabled 且文案转「创建中…」；新增 `.create-dialog__actions`（右对齐、`--app-space-sm` 间距），页内不另写按钮皮肤。验证：真实 `/cases` 页面 CDP 截图 + 计算样式。**验证结果**：通过 —— `doodle-btn--paper` / `doodle-btn--yellow`，`border-radius: 2px`、`box-shadow: 3px 3px 0 0` 墨色、`font-weight: 800`、`min-height: 32px`；提交中态实测 `is-disabled` + 灰影且不可重复点击。
- [x] 1.2 提交路径回归：`confirmCreate` 仍先 `validate()` 再 `addProject`，成功后关弹窗并 `router.push` 到项目表。验证：探针慢速 POST 触发提交中态、放行后跳转 `/cases/projects/9`。**验证结果**：通过。

## 2. 库类型分段控件

- [x] 2.1 `style.css` 的 `el-radio-button` 皮肤改为真实 `2px solid var(--ink)` 墨边 + `outline: none` + 段间 `gap: var(--app-space-xs)` + `14px / 700`；未选中 `--app-text-secondary`、hover 提为 `--app-text-primary`、选中 `--c-dashboard` 底墨字无影。验证：计算样式实测两段 `border: 2px solid`、`border-radius: 4px 8px`、`font-weight: 700`，未选中字色 `rgb(107, 107, 116)`、选中底 `rgb(247, 201, 72)`。**验证结果**：通过。
- [x] 2.2 选中态声明补 `!important`：基础底色带 `!important` 时，弱一档的选中底色会被压掉（首轮实测两段都退成纸色）。验证：修正后选中态底为柠黄。**验证结果**：通过（并把坑登记回 doodle-craft `form-controls.md` §4）。
- [x] 2.3 键盘焦点不失明：EP 的 `:focus-visible` 焦点环画在内层 `outline` 上，随 `outline: none` 一起被撤，补 `.el-radio-button__original-radio:focus-visible + .el-radio-button__inner { outline: 2px solid var(--c-dashboard); outline-offset: 2px }`。验证：Tab 聚焦后实测 `outline: rgb(247, 201, 72) solid 2px`、offset `2px`，截图可见焦点环。**验证结果**：通过。

## 3. 输入件几何（同弹窗内的顺带对齐）

- [x] 3.1 `el-textarea__inner` 并入 `.el-input__wrapper` 那组墨边声明（背景 / `2px` 墨边 / `--app-radius-sm` / `--app-space-sm` 内边距 / hover 与 focus 柠黄语言）。验证：弹窗内单行框与多行框实测同为 `2px solid rgb(30, 30, 36)`。**验证结果**：通过。

## 4. 门禁与验收

- [x] 4.1 `cd frontend && npx vue-tsc --noEmit` 退出码 0。**验证结果**：通过。
- [x] 4.2 `cd frontend && npm run lint:styles` 与 `npm run lint:lines` 退出码 0（批 1–4 全通过、虚线 0 处）。**验证结果**：通过。
- [x] 4.3 `cd frontend && npx eslint src/modules/case-manager/ProjectList.vue`、`npx prettier --check src/style.css src/modules/case-manager/ProjectList.vue` 均无问题。**验证结果**：通过。
- [x] 4.4 `cd frontend && npx vitest run tests/case-manager` 20 passed。**验证结果**：通过。
- [x] 4.5 视觉证据：`temps/browser_shots/create-dialog-before-auto.png`（改前）对 `create-dialog-after-auto.png`（改后）、`create-dialog-after-func.png`（选中「功能」）、`create-dialog-after-focus.png`（键盘焦点）、`create-dialog-after-busy.png`（提交中）、`create-dialog-compare.png`（左右对照）。**验证结果**：通过。
