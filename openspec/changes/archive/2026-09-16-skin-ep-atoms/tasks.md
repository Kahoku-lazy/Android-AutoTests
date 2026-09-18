## 1. tokens.css —— Element Plus 变量覆盖

- [x] 1.1 `--el-color-danger` 改为 `var(--color-red-46)`，并补齐 `--el-color-danger-light-3/5/7/8/9` 与 `--el-color-danger-dark-2`（引用 `--color-red-49/85/95/29`）；验证：Chromium 实测实心 danger `5.97`、plain danger `5.14`、实心 hover `4.70`，均 ≥4.5:1（BEFORE 分别为 1.69 / 1.52 / —）
- [x] 1.2 补齐 `--el-color-error` 与 `--el-color-error-light-3/5/7/8/9`（引用同一红色族）；验证：`el-alert--error` 标题色不再等于 EP 离板色 `rgb(245,108,108)`，标题对比度 16.58
- [x] 1.3 补齐 `--el-fill-color` 与 `--el-fill-color-darker`（引用暖灰 `--color-orange-76`）；验证：`el-skeleton__item` 计算底色由冷灰 `rgb(240,242,245)` 变为暖灰 `rgb(216,210,196)`
- [x] 1.4 补齐 `--el-switch-on-color`（成功色）与 `--el-switch-off-color`（离线灰）；验证：两态不再回落到 EP 默认的 primary / border-color(墨色)
- [x] 1.5 顺带补 `.el-form-item__error` 的文字色（EP 用 `--el-color-danger`，与按钮底色耦合）；验证：实测对比度 **5.90**（有效背景为纸面 `rgb(255,254,245)`）

## 2. style.css —— 分段控件与开关几何

- [x] 2.1 新增 `.el-radio-button__inner { border-radius: var(--app-radius-sm) !important }`；验证：Chromium 实测首/中/末三项圆角均由 `0px/0px/0px/0px` 变为 `4px/8px/4px/8px`
- [x] 2.2 新增选中态规则（柠黄底 + 墨字 + 墨边框，对齐 `.ac-tabs` 口径）与 hover 文字色；验证：选中态对比度 **10.58**（BEFORE 为白字压柠黄），hover 16.58
- [x] 2.3 新增 `.el-switch__core { border-radius: var(--app-radius-sm); border: 2px solid var(--ink) }`；验证：轨道圆角由 EP 默认 `10px` 对称变为 `4px/8px` 不对称

## 3. 门禁与验收

- [x] 3.1 `npm run lint:styles` 退出码 0；验证：批 1/2/3 全绿 —— 新增 `--el-*` 声明全部为 `var()` 引用，无字面量（G2「非原子声明无纯色字面量」通过）
- [x] 3.2 `npx vite build --mode development` 通过（`built in 42.54s`，退出码 0）；验证：既有 `tests/dashboard/**` / `store.ts` / `ProjectTree.vue` 无关报错未新增（本变更未触碰任何 `.ts`）
- [x] 3.3 Chromium 复测（与 BEFORE 同一脚本口径，共 **14 项断言全 PASS**）：danger 实心 5.97 / plain 5.14 / hover 4.70、主色按钮回归 10.58（未受影响）、表单错误 5.90、alert 错误面脱离离板色、radio 三项圆角非零且选中态 10.58、switch 轨道圆角 4px/8px、skeleton 暖灰。**限制**：契约级验证（真实 EP CSS + 项目 CSS + 复刻 EP 标记结构），未加载真实运行中的应用与数据
- [x] 3.4 `git diff --name-only` 本变更部分仅 2 个文件：`frontend/src/shared/styles/tokens.css`、`frontend/src/style.css`，与 `proposal.md` 的 Impact 段一致；工作区其余改动属变更 1/2/3 与其他在飞工作，未触碰

## 4. 过程中修正的两处认知偏差（如实登记）

- [x] 4.1 **机制表述修正**：`var()` 替换为 6 值后并非"整条声明被丢弃"，而是**在 computed-value 阶段失效并回落 initial(0)**；此时该声明已在层叠中胜出，低特异性后置规则无法接管 —— 因此首次用 `.el-radio-button__inner`（(0,1,0)）修复无效，改用 `!important` 才生效。已在 `design.md`/`proposal.md`/delta spec 中更正表述
- [x] 4.2 **测量口径修正**：初版探针把透明背景当作黑色，误判表单错误文字对比度为 3.52；改为沿 DOM 上溯取首个不透明背景（有效背景 `rgb(255,254,245)`）后为 5.90，属达标