## Context

- 本变更的判据来自**浏览器实测**而非静态猜测：用 Playwright + Chromium 加载 `element-plus/dist/index.css` 与项目的 `tokens.css` / `style.css` / `workbench-theme.css`，渲染真实 EP 标记结构，读取 `getComputedStyle` 并按 WCAG 相对亮度公式计算对比度。基线见 `proposal.md` 的表。
- 圆角退化的机制（已在 EP CSS 中定位）：`tokens.css` 的 `--el-border-radius-base: 4px 8px` 是两值；EP 有 3 处把它与额外值组合 ——
  - `.el-radio-button:first-child .el-radio-button__inner { border-radius: var(--el-border-radius-base) 0 0 var(--el-border-radius-base) }`
  - `.el-radio-button:last-child .el-radio-button__inner { border-radius: 0 var(--el-border-radius-base) var(--el-border-radius-base) 0 }`
  - `.el-radio-button__original-radio:focus-visible+.el-radio-button__inner { border-radius: var(--el-border-radius-base) }`（此条为单值替换，合法）
  替换后成为 6 值，该声明在 **computed-value 阶段失效并回落 initial(0)**。关键：失效发生在计算阶段，声明本身已在层叠中胜出，因此低特异性的后置规则**无法接管** —— 修复必须用同等/更高特异性（本变更用 `!important`，与 `style.css` 对 EP 类的既有约定一致）。
- `el-radio-button` 的选中态（EP）：`.el-radio-button.is-active .el-radio-button__original-radio:not(:disabled)+.el-radio-button__inner { color: var(--el-radio-button-checked-text-color, var(--el-color-white)); background-color: …var(--el-color-primary); … }` —— 即白字压 `--el-color-primary`（本主题为柠黄 `#f7c948`）。
- `--el-color-danger` 在 EP 中同时承担"实心 danger 底色"与"表单校验错误文字色"（`.el-form-item__error` 取 `--el-color-danger`），因此单点修按钮无法覆盖表单错误文本；改 token 才能一并解决。
- `--el-color-danger-light-5` / `-light-9`、`--el-color-error*`、`--el-fill-color` / `-darker`、`--el-switch-on/off-color` 在 `tokens.css` 中**均无声明**。
- 动机见 `proposal.md`。

## Goals / Non-Goals

**Goals**

- danger 实心/plain 按钮与表单校验错误的对比度不低于 4.5:1
- `el-radio-button` 恢复非零圆角（取自 `--app-radius-*`）且选中态与项目分段控件同口径、可读
- `el-skeleton` / 浅底不再使用 EP 冷灰
- `el-switch` 轨道几何与开/关配色落到主题
- `el-alert` 错误面不再使用 EP 离板红
- 所有新增 `--el-*` 覆盖引用主 token 原子（`lint:styles` 的 EP 覆盖规则不出现字面量）

**Non-Goals**

- 不改 `--el-border-radius-base` 的值（它是两值的**有意**不对称几何，且 39 处直接使用处工作正常）；本次只对**组合使用**该变量的原子显式补圆角
- 不替换 `element-locator` 的 `el-alert` 调用点为共享 `ErrorState`（属变更 6 的调用点统一）
- 不收敛 `FilterTabs` 的 `999px` 与其余圆角字面量（变更 10）
- 不为 EP 原子新增主题令牌家族（复用既有 `--color-*` / `--app-*`）

## Decisions

**D1 danger 走 token 层而非按钮层**
理由：`--el-color-danger` 同时是"实心按钮底色"和"表单错误文字色"，改 token 一次覆盖三条路径（实心、plain、表单提示），且不会与 `workbench-theme.css` 的 `.wb-btn.el-button--danger` 皮肤冲突（后者用显式声明，天然胜过变量驱动的基类规则）。
备选：在 `style.css` 写 `.el-button--danger { … !important }` —— 否决：漏掉表单错误文字，且会以 `!important` 压过 `.wb-btn` 的既有 danger 皮肤，产生连带改动。
取值：`--el-color-danger: var(--color-red-46)`（#b23838），即项目既有的 `--app-status-danger-text`；浅色档取 `--color-red-85` / `--color-red-95`。

**D2 `el-radio-button` 按"每项独立不对称圆角"处理**
理由：两值变量参与组合必然非法，最稳的修法是显式声明；项目对 tab 类控件的既有口径就是每项 `--app-radius-sm`（见 `.ac-tabs .el-tabs__item`），保持一致。
备选：把 `--el-border-radius-base` 改成单值 —— 否决：会改变 39 处直接使用该变量的 EP 原子几何，回归面过大。

**D3 `el-radio-button` 选中态取"柠黄底 + 墨字"**
理由：与 `workbench-theme.css` 的 `.ac-tabs .el-tabs__item.is-active` 完全同口径（黄底墨字），既解决"白字压柠黄"，又让分段控件与标签页在观感上统一。
备选：把 `--el-radio-button-checked-*` 变量改掉 —— 可行但会同时影响未在本主题作用域内的用法；显式规则更可控。

**D4 `--el-fill-color` 映射到暖灰 `--color-orange-76`**
理由：该原子已登记且本就是项目的暖中性灰（纸面点纹与图钉中间色同源），比 EP 冷灰 `#f0f2f5` 更贴合纸面。
备选：映射到 `--color-lime-94`（`--el-fill-color-light` 已用）—— 否决：在暖白纸面上几乎不可见，骨架会"消失"。
风险见下节。

**D5 `--el-color-error*` 取项目红色族而非保留 EP 默认**
理由：规格要求错误面使用已登记原子；EP 的 `#f56c6c` / `#fef0f0` 从未登记进调色板，属离板色。

## Risks / Trade-offs

- [`--el-fill-color` 影响面较广（骨架、浅底标签、部分 EP 内部浅底），从冷灰变暖灰] → 变更是"统一到纸面族"，方向与主题一致；tasks 含受影响原子的 Chromium 复测，若有原子明显失衡可只回退该条
- [实心 danger 按钮由浅桃底变深红底，观感与 `--c-runner` 桃粉不再同色] → 这是可读性换来的有意取舍；桃粉仍用于 `--c-runner` 强调与 `--app-status-danger` 填充，语义未被移除；tasks 含对比度断言
- [显式 `.el-radio-button__inner` 圆角可能影响"首尾项相连"的视觉连体感] → 项目分段控件的既有口径本就是每项独立圆角（`.ac-tabs`），且当前是 0 圆角（更差）；tasks 含三项（首/中/末）渲染断言
- [新增 `--el-*` 声明若写成字面量会被 `lint:styles` 拦截] → 全部引用 `--color-*` / `--app-*`；tasks 含 `lint:styles` 退出码校验

## Migration Plan

1. 先改 `tokens.css` 的 EP 变量（danger / error / fill / switch），再改 `style.css` 的 `el-radio-button` 与 `el-switch` 几何
2. 用同一套测量脚本复测 BEFORE/AFTER，逐项确认对比度 ≥4.5:1 与圆角非零
3. 回滚策略：纯主题覆盖，回滚即 `git revert`；无数据、接口与路由迁移

## Open Questions

（无）