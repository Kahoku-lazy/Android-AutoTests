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
