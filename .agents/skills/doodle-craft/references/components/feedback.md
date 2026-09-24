# 反馈规格 — 三态共享件与消息提示

三态分工是硬规则：**加载 → 骨架；取数失败 → 错误件（带重试）；取数成功但为空 → 空态**。加载期间**不得**渲染空态（假空态）。

**以代码为准**：`frontend/src/shared/components/patterns/**` + `frontend/src/style.css`。令牌值见 [../tokens.md](../tokens.md)。

## 1. SkeletonCard 加载骨架

| 维度 | 规格 |
|------|------|
| 容器 | 无框无底 |
| 骨架条 | 圆角 `--app-radius-sm`；`variant` `card`（默认，4 条）/ `list` |
| a11y | `role="status" aria-label="加载中"` |
| 减动效 | 关 animation |

**已知**：shimmer 两级灰令牌同值 → 实际渲染是纯灰块、无流光（见 [../known-gaps.md](../known-gaps.md)）。**禁用**全屏 spinner、模块私有 shimmer / `__loading` 容器、裸 `el-skeleton`。

## 2. ErrorState 取数失败

| 维度 | 规格 |
|------|------|
| 容器 | 底 `--app-error-bg`、框 `2px solid --app-status-danger`、圆角 `--app-radius-md`、无阴影 |
| 文字 | `--app-size-sm` / 600 / `--app-status-danger-text` |
| 重试按钮 | 白底墨框，hover `--app-highlight` + `translate(1,1)` |

**已知**：无 `role="alert"`。**禁用**白屏、用 `el-alert` 顶替错误态。

## 3. EmptyState 空态

| 维度 | 规格 |
|------|------|
| 容器 | 无框；内边距 `48px 24px` |
| 图标 | 40px（登记图形例外，opacity .5）|
| 文字 | `--app-size-md` / 700 |
| 提示 | `--app-size-sm` / `--app-text-secondary` |
| 插槽 | `default` 放 CTA |

## 4. el-message 消息提示

底 `--app-bg-card`、圆角 `--app-radius-sm`、框 `2.5px solid var(--ink)`、影 `2px 3px 0 rgba(0,0,0,0.06)`。用于"操作已受理/已创建"一类**短反馈**，不承担错误态职责。

**el-alert**：**未覆盖**；错误面配色经 `--el-color-error*` → 项目红色族（`--color-red-46` / `-49` / `-85` / `-95` / `-29`）。仅在需要**内联告警块**时使用，取数失败仍走 `ErrorState`。

## 5. 原地异步（弹窗/抽屉内）

弹窗、抽屉、面板内的**原地**异步操作（保存、加载子内容）可用 `v-loading`；表格加载走 `AppTable` 的 `loading`。三态共享件用于**页面级取数**，两者不混用。
