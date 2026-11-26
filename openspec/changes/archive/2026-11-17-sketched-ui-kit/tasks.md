## 1. 技能（先改规则，再改代码）

- [x] 1.1 新增分类文件 `references/components/sketched-ui-kit.md`：按钮五态、输入四态、label、用法、线型白名单、反模式。验证：文件存在且被 SKILL.md 组件目录引用。**验证结果**：已建并登记。
- [x] 1.2 `SKILL.md` §线型规则：白名单加「手稿控件皮肤」，判据加第 2 条，虚线口径分两类，违规判定改为"只有 `AgentRouteCard.vue` 与 `sketched-kit.css` 可出现 dashed"。验证：`grep dashed` 口径与门禁 OWNERS 一致。**验证结果**：一致。
- [x] 1.3 `SKILL.md` 组件目录加「手稿控件（分类）」行、选型判据加一行、硬规则 11 增补"已登记分类是唯一例外"、自检清单加两条。验证：无自相矛盾表述。**验证结果**：已改。
- [x] 1.4 `README.md` 目录结构登记新类目，使用说明第 1 条同步白名单。**验证结果**：已改。
- [x] 1.5 `references/tokens.md`：§1.6 线型登记同步，新增 §1.18 手稿控件令牌表（含声明处一列）。**验证结果**：已改。
- [x] 1.6 `components/general.md`（DoodleBtn 的 kit 变体）、`components/form-controls.md`（输入框 kit 变体）互链。**验证结果**：已改。

## 2. 令牌与样式表

- [x] 2.1 `shared/styles/tokens.css` 增 `--comp-kit-*` 颜色 / 半径 / focus 环原语（不含 `dashed` 字面量）。验证：`tokens.css` 内 `dashed` 计数为 0。**验证结果**：`npm run lint:lines` 报 0 个文件 / 0 处。
- [x] 2.2 新增 `shared/styles/sketched-kit.css`：输入框四态 + 多行 + label + `.sketch-form` / `.sketch-field` 骨架 + 按钮五态 + 减动效块；虚线组合值声明在 `.sketch-kit` 作用域内。**验证结果**：`lint:styles` 批 2 通过、批 3 无新增（仍为既有 21 处 `task-list` 越界借用）。
- [x] 2.3 `main.ts` 引入该样式表（放在 `workbench-theme.css` / `motion.css` 之后）。**验证结果**：`npx vue-tsc --noEmit` 0 错误。

## 3. 门禁

- [x] 3.1 `tests/check-dashed-whitelist.mjs`：OWNERS 增加 `shared/styles/sketched-kit.css`，头注释、报错文案同步为两个落点。验证：`npm run lint:lines`。**验证结果**：`[dashed] 虚线出现在 0 个文件 / 0 处（白名单组件 2 个）` → 通过。
- [x] 3.2 负向验证：任一非白名单文件加 `dashed` 仍应失败。**验证结果**：首次落地把虚线组合值写在 `tokens.css` 时，门禁即报 `shared/styles/tokens.css：dashed 4 次` 并退出 1，证明拦截有效。

## 4. 首个消费方（运营后台「新建模型」抽屉）

- [x] 4.1 `model-configs.vue` 抽屉内容根加 `.sketch-kit` + `.sketch-form`，字段改用 `.sketch-field` / `.sketch-field__label`，动作区改用 `.sketch-form__actions`，删除本页自带的 `.ops-form` / `.ops-field` 皮肤。**验证结果**：页面 scoped 样式只剩名称行列表布局。
- [x] 4.2 模型名称仍是「一行一个输入行 + 删除 + 添加一行」，与上一轮一致，只是外观切到 kit。**验证结果**：逻辑未改，`namesInForm()` 不变。
- [x] 4.3 `npx eslint src/modules/ops-console/model-configs.vue` 与 `npx vue-tsc --noEmit`。**验证结果**：两者均 0 错误。

## 5. 文档与验收

- [x] 5.1 本变更 `proposal.md` / `design.md` / `tasks.md` / `specs/frontend-doodle-sketched-ui-kit/spec.md`。验证：`openspec validate sketched-ui-kit --strict`。**验证结果**：见下条。
- 【已取消 · 人工验收不做】5.2 目视验收：打开「运营 → 模型配置 → 新建模型」，确认按钮五态、输入框虚线、label 字距、名称行列表与新皮肤自洽；任一主线页面（如用户管理）外观未变。**未完成**：本机沙箱禁止浏览器子进程（`spawn EPERM`）与 `run.py start`（`adb.exe` 读取被拒），无法截图比对，需需求方本地确认。

## 6. 审核收口（2026-11-16，按 StyleKit `hand-drawn-doodle` LINT RULES 反向审查后）

- [x] 6.1 焦点语言统一：输入框 focus 由 `box-shadow` 扩散环改为与按钮同一套 `2px solid var(--c-dashboard)` outline + `2px` offset；删除已无消费方的 `--comp-kit-focus-ring` 令牌。验证：`grep -rn "comp-kit-focus-ring" frontend/src` 为 0。**验证结果**：见 6.3。
- [x] 6.2 焦点指示自持：给 `.el-input__inner` / `.el-textarea__inner` / `.el-select__wrapper` / `.el-select__input` 显式 `outline: none`，不再依赖 EP 出厂行为，避免升级后出现双重焦点框。**验证结果**：见 6.3。
- [x] 6.3 门禁：`npm run lint:styles`（批 2 通过、批 3 无新增）· `npm run lint:lines` · `npx vue-tsc --noEmit`。**验证结果**：三条全绿（批 3 仍为既有 21 处 `task-list` 越界借用）。
- [x] 6.4 改动范围确认：`.sketch-kit` 目前唯一消费方是 `modules/ops-console/model-configs.vue:232`，本轮改动全部写在 `.sketch-kit` 作用域内，未触碰 `style.css` / `DoodleBtn.vue` / `--el-*` / 字体栈。**验证结果**：`grep -rn "sketch-kit" frontend/src` 仅命中 kit 样式表、tokens 注释与 `main.ts` 引入。
- [x] 6.5 EP 2.14 选择器补全：实测安装版本 `element-plus@2.14.7` 的 select 根节点是 `.el-select__wrapper`（不是旧版 `.el-select .el-input__wrapper`），kit 的选择器补齐 hover / focus / disabled，否则「厂商」下拉会退回 EP 实线皮肤。验证：预览页 `getComputedStyle(.el-select__wrapper).borderTopStyle === "dashed"`。**验证结果**：`dashed 1px .../0.3` + `radius 3px`。
- [x] 6.6 选中值着色与行内按钮挤压：`.el-select__placeholder` 只在带 `is-transparent`（真空态）时用弱色，避免已选中的「deepseek」显示成灰占位；行内「删除」按钮补 `flex: 0 0 auto` + `white-space: nowrap`（此前被压成两字竖排，实测 62×34）。**验证结果**：计算值 `placeholderColor = rgb(30,30,36)`（墨色）；按钮 `62×34`。
- [x] 6.7 真实渲染取证：用 `vue.global.js` + `element-plus/dist/index.full.js` + 仓内 `tokens.css` / `sketched-kit.css` 在 file:// 下渲染同构抽屉并截图（`temps/stylekit/preview.html`、`shoot.mjs`、`metrics.mjs`），逐项核对：输入框与按钮焦点计算值均为 `solid 2px / offset 2px / rgb(247,201,72)`，内层 input `outline: none`。**验证结果**：见 6.5 / 6.6 的计算值。
- 【已取消 · 未做取消】6.8 待定：Chrome 把 `border-width` 舍入到整数 CSS px（`1.5px → 1px`、`2.5px → 2px`，DPR 1/2 实测一致），所以文档写的 `1.5px dashed` 实际画的是 `1px`。是改 `2px`（更接近参考图）还是把文档改成 `1px`，等需求方定。

## 7. 观感调整 + 保存按钮绿渐变（2026-11-16，需求方看图后追加）

- [x] 7.1 **修作用域选择器失效**：`.sketch-kit` 与 `.sketch-form` 原挂在同一元素上，而 kit 全是后代选择器 → 表单骨架/字段间距从未生效（这是"字段挤在一起"的根因）。改为外层 `.sketch-kit` + 内层 `.sketch-form`，模板与技能文档示例同步。验证：`.sketch-form` 计算值 `display: flex`、`row-gap: 16px`；字段间距实测 16px、foot→地址 20px。**验证结果**：`footToAddressLabel 20px`。
- [x] 7.2 行内「删除」与输入框等高：行容器改 `align-items: stretch`，去掉写死的按钮高度。验证：`btnHeight 38 === inputHeight 38`，水平间距 8px。**验证结果**：通过。
- [x] 7.3 label 行内小按钮收紧：「加载模型」压到 28px + 12px 字，避免把 label 行撑高、字段标题与控件脱节。验证：`labelButtonHeight 28`。**验证结果**：通过。
- [x] 7.4 保存按钮改为**绿色由深到淡的渐变填充**：新增 `--comp-kit-save-from` / `-to` / `-gradient`（成功色 `color-mix` 派生，不新增颜色原子）与 `.doodle-btn--save` 变体；几何沿用填充态（实线墨边 + 硬影）。验证：计算值 `linear-gradient(rgb(98,190,108), rgb(184,225,181))`、`border solid 2px`、`box-shadow 3px 3px 0 0`。**验证结果**：通过。
- [x] 7.5 文档与规格同步：`sketched-ui-kit.md`（Commit 变体、渐变属已批准偏离、同元素挂类的反模式）、`tokens.md` §1.18 三个令牌、本变更 spec（新增"保存按钮绿渐变"需求 + 作用域同元素场景）。验证：`openspec validate sketched-ui-kit --strict`。**验证结果**：见 7.6。
- [x] 7.6 门禁：`npm run lint:lines` · `npm run lint:styles` · `npx vue-tsc --noEmit` · `npx eslint`。**验证结果**：`lint:lines` 通过（虚线仍只在 2 个白名单落点）；批 2 通过、批 3 与基线一致（21 处既有）；tsc / eslint 0 错误；`openspec validate` valid。
- [x] 7.7 真实渲染复核：用真实 Vue + EP 2.14.7 重出图（默认 / 焦点 / 行列表 / 动作区），确认渐变、等高、间距。**验证结果**：`temps/stylekit/kit-default.png` 等。

## 8. 第二轮观感（2026-11-16，需求方看完真机截图后）

- [x] 8.1 保存按钮与「取消」同一套几何：边框改回虚线 `var(--comp-kit-border)`、去掉硬影，只保留绿渐变填充；hover/active 用亮度微调（换底色会把渐变冲掉）。验证：`borderTopStyle=dashed`、`boxShadow=none`，与 `--paper` 计算值逐项相等。**验证结果**：见 8.4。
- [x] 8.2 字段标题放大成墨色：`.sketch-field` 由 `12px + 次级灰 + 0.08em 字距` 改为 `--app-size-sm`(14px) + `--ink` + 无字距，与「+ 添加一行」等按钮文字同档；删除不再被引用的 `--comp-kit-label-ink` 令牌。验证：label 计算值 `font-size 14px`、`color rgb(30,30,36)`。**验证结果**：见 8.4。
- [x] 8.3 去掉名称行 placeholder：`el-input` 不再传 `:placeholder`（原来会显示「模型名称 1，如 deepseek-flash」）。**验证结果**：模板已无该绑定。
- [x] 8.4 复核与门禁：真实渲染出图 + `lint:lines` / `lint:styles` / `vue-tsc` / `eslint` / `openspec validate --strict`。**验证结果**：全绿（批 3 仍为既有 21 处）。
- [x] 8.5 label 行内按钮不再缩字：去掉 12px 特例，只压高度（28px），字号与其它按钮同档 14px。验证：`labelButtonHeight 28`、字号继承 kit 基值 `--app-size-sm`。**验证结果**：通过。

## 9. 字段顺序（2026-11-16）

- [x] 9.1 「地址」上移到「厂商」下面：字段顺序改为 厂商 → 地址 → 密钥环境变量 → 模型名称。只改模板顺序，表单结构与间距规则不变。验证：`vue-tsc` / `eslint` 0 错误，重新出图确认。**验证结果**：通过。

## 10. 字段顺序定稿（2026-11-16）

- [x] 10.1 撤销 9.1 的顺序并定稿：**厂商 → 密钥环境变量 → API 地址 → 模型名称**；「地址」标签改名为「API 地址」。只动模板，字段绑定 `form.base_url` 与校验不变。验证：`vue-tsc` / `eslint` 0 错误，重新出图确认。**验证结果**：通过。


