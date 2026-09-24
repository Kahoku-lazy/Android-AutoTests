# 通用组件规格 — 按钮族与标签

维度 × 实际规格。**以代码为准**：`frontend/src/style.css`（EP 全局覆盖）· `frontend/src/shared/styles/workbench-theme.css`（`.wb-shell` 内的共享皮肤）· `frontend/src/shared/components/**`。令牌值见 [../tokens.md](../tokens.md)。

> **读法**：标「未覆盖」= 该维度没有主题声明、走 Element Plus 出厂值。需要时按主题规则补令牌，**不要照抄出厂值**。

## 1. Button 按钮（Element Plus 全局覆盖）

| 维度 | 实际规格 |
|------|----------|
| 圆角 | `--app-radius-sm`（`4px 8px`）|
| 字体 | `--app-font` |
| 字号 / 字重 / padding / 高度 / disabled | **未覆盖**（走 EP 默认；页头按钮由 `WorkbenchHeader` 局部收紧为 800 字重 + `2.5px` 边框 + `5px 14px`）|
| 默认态 | 边框经 `--el-border-color` → `--ink`；底色经 `--el-fill-color-blank` → 白 |
| primary | 底 `--c-dashboard`、框 `2.5px solid var(--ink)`、字 `--ink`、字重 700、硬影 `2px 2px 0 rgba(0,0,0,0.06)` |
| primary hover | 底 `--app-highlight` |
| active（所有按钮）| `transform: scale(0.97)`，`transform --app-duration-fast --app-ease` |
| success / danger / danger plain | **全局未覆盖**；语义色只在 `.wb-shell .wb-btn` 变体里（下表）|

**`wb-btn`（工作台按钮：页头与操作区）**：圆角 `--app-radius-sm`、字重 700、框 `2px solid var(--ink)`、底 `--app-bg-card`、字 `--ink`、影 `--app-shadow-sm`；hover 底 `--c-dashboard` + `translate(1px,1px)`。

| 变体 | 规格 |
|------|------|
| `--primary` | 底 `--c-dashboard` |
| `--success` | 底 `--c-device` |
| `--danger` | 底 `--app-status-danger-bg` / 字 `--app-status-danger-text` / 框 `--c-runner`，hover `--app-btn-hover-danger` |
| `wb-btn--sunset` | 底 `#f0c090` / 框 `#d8a870` / 字 `#fff` / hover `#f5cda0` —— **字面量存量**（登记在 `motion.css`）；新增同类变体请改用令牌 |

**约束**：一个操作区最多一个 primary；危险操作放确认弹窗（`ConfirmButton` 或 `ElMessageBox`）。

## 2. DoodleBtn 涂鸦按钮

原生 `<button>`，自包含样式：

```
边框 2.5px solid var(--ink)   圆角 2px   阴影 3px 3px 0 0 var(--ink)
min-height 32px   padding 0 14px   字 --app-size-sm(14px) / 800
```

- **tone**：`paper`（默认，底 `--paper`）/ `teal`（`--c-case`）/ `yellow`（`--c-dashboard`）/ `danger`（`--app-marker-red` + 白字）
- hover `translate(-1,-1)` + 影 4px；active `translate(2,2)` + 影 1px；focus-visible 2px outline
- **disabled**：底 `--comp-dbtn-disabled-bg`、字 `--comp-dbtn-disabled-ink`、影 `3px 3px 0 0 #bbb`（字面量）+ `:disabled` 属性 + JS 拦截
- **用途**：内容卡操作区。页头 `wb-btn` 与 EP 表单主按钮**不换**成这个

## 3. ConfirmButton 确认按钮

`doodle=true` → 渲染 `DoodleBtn tone="danger"`；否则渲染 `el-button`（透传 `$attrs`）。确认框统一走 `ElMessageBox`（`type` 默认 `warning`，见 [overlays.md](overlays.md)）。props：`message` / `title` / `confirmText` / `type` / `doodle` / `disabled`；emit `confirm` / `cancel`。**禁止** `window.confirm`。

## 4. Tag 标签

圆角 `--el-border-radius-small`（`3px 6px`）、字重 700；字号与边框**未覆盖**。状态配色见 [../tokens.md](../tokens.md) §1.3：成功 `--app-status-success-*`、失败 `--app-status-danger-*`、锁定 `--app-status-purple-*`、等待 `--app-status-warning-bg` + `--app-warning-text`、离线 `--app-offline` + `--app-text-secondary`。

## 附：按钮相关的 EP 变量

`--el-color-primary` → `--color-yellow-63`（柠黄，**不是 EP 蓝**；AI 模块在 `.ai-workbench` 内改写为 `--color-purple-73`）；`--el-color-danger` / `-error` → `--color-red-46`；`--el-border-radius-base` = `4px 8px`；`--el-border-radius-small` = `3px 6px`。完整 41 条映射见 [../tokens.md](../tokens.md) §1.17。
