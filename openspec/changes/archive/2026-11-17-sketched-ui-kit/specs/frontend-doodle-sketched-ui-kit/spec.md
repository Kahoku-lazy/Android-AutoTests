## Purpose

提供一套按作用域生效的手稿控件皮肤（按钮五态 + 输入四态），让手稿 / 纸片语境的表单与工具条有明确、可复用、可机械校验的外观规则，同时把虚线从"只属于助手角色卡"收敛为"控件级白名单"，不放宽到卡片、表纸、弹窗与抽屉外框。

## ADDED Requirements

### Requirement: 手稿控件皮肤是可选分类且按作用域生效

系统 SHALL 提供一个名为 `Sketched UI Kit` 的控件级皮肤分类，且 MUST 只在挂了作用域根类 `.sketch-kit` 的子树内生效。未挂该类的页面与组件 MUST 保持主线皮肤（`DoodleBtn` 实线描边 + 硬影、`el-input` 实线墨边），外观零变化。该分类 MUST NOT 通过改 `DoodleBtn` 组件本体或全局 `--el-*` 生效。kit 的结构类（`sketch-form` / `sketch-field` / `sketch-form__actions`）MUST 位于作用域根的后代节点上，MUST NOT 与 `.sketch-kit` 挂在同一个元素上（kit 的选择器是后代选择器，同级不命中）。

#### Scenario: 作用域内切到手稿皮肤

- **WHEN** 某个容器带上 `.sketch-kit` 并渲染 `DoodleBtn` 与 `el-input`
- **THEN** 该容器内的按钮描边态为虚线且无硬影，输入框为浅墨虚线边
- **AND** 容器外部同页面的按钮与输入框仍为实线主线皮肤

#### Scenario: 未挂作用域不留痕

- **WHEN** 页面没有挂 `.sketch-kit`
- **THEN** 页面渲染结果与改造前逐项一致（虚线条数为 0）

#### Scenario: 结构类与根类同元素时不会静默生效

- **WHEN** 把 `.sketch-kit` 与 `.sketch-form` 写在同一个元素上
- **THEN** 该写法不满足 kit 的生效条件（后代选择器不命中），实现 MUST 改为外层根 + 内层结构类

### Requirement: 按钮五态

在 `.sketch-kit` 作用域内，按钮 SHALL 复用 `DoodleBtn` 的既有 tone 表达五种外观：Primary（`paper`）、Danger（`danger`）、Highlight（`yellow`）、Disabled（任意 tone + `disabled`）、Teal（`teal`）。描边态（Primary / Danger / Disabled）MUST 使用 `1.5px` 虚线边框且 MUST NOT 带硬偏移阴影；填充态（Highlight / Teal）MUST 保持 `2.5px solid` 墨边 + `3px 3px 0 0` 硬影。Danger 的文字色 MUST 使用 `--comp-kit-danger-ink`（纸底对比度 ≥ 4.5:1），MUST NOT 使用 `--app-marker-red`。键盘焦点 MUST 可见。

#### Scenario: 描边态无影、填充态有影

- **WHEN** 在作用域内分别渲染 `tone="paper"` 与 `tone="yellow"`
- **THEN** `paper` 按钮为虚线边框且不显示阴影位移
- **AND** `yellow` 按钮为实线墨边 + 右下硬影

#### Scenario: 危险按钮改为红虚线描边

- **WHEN** 在作用域内渲染 `tone="danger"`
- **THEN** 按钮为纸底 + 红虚线边框 + 红色文字（不是实心红底白字）
- **AND** 文字色取 `--comp-kit-danger-ink`

#### Scenario: 禁用态虚线更淡

- **WHEN** 作用域内按钮处于 `disabled` 或 `.is-disabled`
- **THEN** 边框为最淡虚线、底色为浅纸底、文字为次要色，且无阴影与位移

#### Scenario: 键盘焦点可见

- **WHEN** 作用域内按钮通过键盘获得焦点
- **THEN** 出现 2px 可见 outline 环，offset 为 2px

### Requirement: 保存按钮使用绿色渐变填充

作用域内的保存 / 提交按钮 SHALL 可加 `doodle-btn--save` 修饰类：**几何 MUST 与 Primary 描边态完全一致**（虚线边框、无位移、无硬影），差异只允许在填充上——底色为**由深到淡的绿色渐变**。渐变两端 MUST 由 `--comp-kit-save-from` / `--comp-kit-save-to` 两个令牌给出，色相 MUST 取自成功色（`--app-status-success`），MUST NOT 新增颜色原子或写字面色值。该变体是相对上游 `hand-drawn-doodle`「flat marker colors only」的**已批准偏离**，范围仅限此一个修饰类。

#### Scenario: 保存按钮与取消同一套几何

- **WHEN** 作用域内同时渲染 `doodle-btn--paper`（取消）与 `doodle-btn--save`（保存）
- **THEN** 两者的边框线型、线宽、圆角、高度、内边距、阴影完全一致
- **AND** 仅保存按钮多出绿色渐变填充

#### Scenario: 保存按钮悬停不换底色

- **WHEN** 悬停保存按钮
- **THEN** 渐变保留（仅亮度微调），不出现位移或阴影
- **AND** 不退回 Primary 的纯色 hover 底色

### Requirement: 输入框四态与 label
在 `.sketch-kit` 作用域内，输入框（`el-input` / `el-select` 输入区 / `el-textarea`）MUST 使用 `1.5px` 浅墨虚线边框、`box-shadow: none`、`min-height: 36px`；hover 与 focus 时边框加深；focus MUST 与按钮使用同一套焦点指示（`2px` outline + `2px` offset），且内层控件 MUST 显式 `outline: none`，使焦点框只出现一次；`disabled` 时为浅纸底 + 最淡虚线 + 次要文字色；多行框 MUST 使用同一虚线并允许纵向缩放。字段 label MUST 与动作按钮文字同档（`--app-size-sm` = 14px）、颜色取墨色 `--ink`、不写字距；MUST NOT 使用 12px 以下的字号，也 MUST NOT 再用次级灰当标题色。label 的字距 MUST NOT 继承进输入内容。字段之间的纵向间距 MUST 由 `.sketch-form` 的 `--app-space-md` 统一给出，MUST NOT 依赖元素默认外边距。

#### Scenario: 默认与聚焦

- **WHEN** 作用域内渲染输入框并使其获得焦点
- **THEN** 默认态为浅墨虚线边框、无内发光
- **AND** 聚焦态边框加深，并出现与按钮相同的一套 2px outline（offset 2px）
- **AND** 内层 `input` / `textarea` 不叠加浏览器原生 outline

#### Scenario: 禁用输入框

- **WHEN** 输入框被禁用（如「密钥环境变量」只读展示）
- **THEN** 显示浅纸底 + 最淡虚线边框 + 次要文字色

#### Scenario: 多行框与 label 字号

- **WHEN** 作用域内渲染多行输入与该字段 label
- **THEN** 多行框沿用虚线并可纵向缩放
- **AND** label 字号为 14px（`--app-size-sm`）、颜色为墨色，与动作按钮文字同档

### Requirement: 虚线白名单与门禁同步

虚线 MUST 只由 `shared/styles/sketched-kit.css` 与 `AgentRouteCard.vue` 两处声明。`frontend/tests/check-dashed-whitelist.mjs` 的白名单 MUST 包含该样式表，且卡片、表纸、弹窗与抽屉外框、列表分隔、页面装饰 MUST 仍为实线。虚线颜色 MUST 由 `--comp-kit-*` 令牌声明，MUST NOT 在消费处写裸颜色或"假虚线"（`border-image` / 重复渐变）绕过门禁。

#### Scenario: 门禁拦住越界虚线

- **WHEN** 任一其它文件（含 `style.css` / `tokens.css` / 其它组件）出现 `dashed`
- **THEN** `npm run lint:lines` 失败并列出该文件

#### Scenario: 白名单内允许

- **WHEN** 只有 `AgentRouteCard.vue` 与 `sketched-kit.css` 出现 `dashed`
- **THEN** `npm run lint:lines` 通过

### Requirement: 减少动效降级

作用域内凡在 `transition` 中改变 `transform` 的规则 MUST 提供 `@media (prefers-reduced-motion: reduce)` 降级块；降级后 MUST NOT 依赖位移传达可交互性。

#### Scenario: 减少动效下不位移

- **WHEN** 用户环境为 `prefers-reduced-motion: reduce` 且悬停填充态按钮
- **THEN** 按钮不产生位移，仅保留颜色 / 边框色反馈
