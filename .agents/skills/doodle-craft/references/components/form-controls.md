# 表单控件规格 — 输入 / 选择 / 开关 / 分段控件

维度 × 实际规格。**以代码为准**：`frontend/src/style.css`（EP 全局覆盖）+ `tokens.css` 的 `--el-*` 映射。令牌值见 [../tokens.md](../tokens.md)。

> **读法**：标「未覆盖」= 该维度没有主题声明、走 Element Plus 出厂值。

## 1. Form / Input 表单与输入

| 维度 | 实际规格 |
|------|----------|
| 输入框 wrapper（含 `el-select` 输入区）| 圆角 `--app-radius-sm`、框 `2px solid var(--ink)`、底白、`box-shadow: none` |
| hover / focus | 边框变 `--c-dashboard`；focus 另加 `0 0 0 3px color-mix(--c-dashboard 20%, transparent)` |
| placeholder | **未覆盖**（EP 默认）|
| label 宽度 / 对齐 | **无全局定义**（模块自定，常见 80 / 100 / 120px 三档）|
| 校验错误文字 | `--app-status-danger-text`（对比度 ≥ 4.5:1）|
| textarea | **未覆盖** |

**约束**：需要校验的表单必须 `:model` + `:rules` + `el-form-item prop` + `validate()`；**只有 `required` 没有 `:rules` 属误导性 UI**；实际非必填的字段不许标必填星号；弹窗内单列、宽度 ≤ 520px。

**手稿控件皮肤（`.sketch-kit` 作用域）**：框改 `1.5px dashed var(--comp-kit-line-soft)` 浅墨虚线、无影、`min-height: 36px`；label 12px + `letter-spacing: 0.08em`；禁用态浅灰底 + 更淡虚线；多行框同款虚线 + `resize: vertical`。规格见 [sketched-ui-kit.md](sketched-ui-kit.md) §2，落点 `shared/styles/sketched-kit.css`。

**设备页控制条（`device-pool`）· 已登记的渐变偏离**：筛选下拉与名称搜索 MUST 呈现为输入件、MUST NOT 套按键皮肤——`2px solid var(--ink)` 边框保留，圆角 `var(--app-radius-sm)`，**撤掉硬偏移影**、字重回 `--app-font-weight-regular`；填充取 `--comp-device-field-fill`（135° 斜向，`--c-device` 45% → 20%，令牌见 [../tokens.md](../tokens.md) §1.19）。hover / focus 仍走本节的柠黄语言（模块 `!important` 会压掉全局规则，须在模块内补回）。渐变抬亮底色后 EP 出厂 placeholder 与下拉箭头只剩约 `1.7:1`，两处一并提到 `--app-text-secondary`。落点 `modules/device-pool/DevicePoolView.style.css`；只此一处，**不得**扩散成全局输入框皮肤。

## 2. Select 选择器

输入区同 §1；**下拉弹层未覆盖**（底色经 `--el-bg-color-overlay` → 白）。

## 3. Cascader 级联选择

**无全局覆盖**；`emitPath` 默认 `true`，需要单值时必须显式 `emitPath: false`。

## 4. 分段控件 el-radio-button

圆角 `--app-radius-sm`（**必须 `!important`**：`--el-border-radius-base` 是双值，EP 组合后会生成 6 值非法声明、在 computed-value 阶段回落 0）；选中态 字 `--ink` + 底 `--c-dashboard` + 框 `--ink`；hover 只变字色。与 `AppTabs` 同口径（见 [layout.md](layout.md)）。

## 5. el-switch 开关

轨道圆角 `--app-radius-sm`、框 `2px solid var(--ink)`；开态色 `--app-status-success`、关态色 `--app-offline`（替代 EP 默认"开=primary / 关=边框色"）。

## 6. Tabs

无全局 `.el-tabs` 覆盖；工作台内用 `AppTabs`（见 [layout.md](layout.md)）。
