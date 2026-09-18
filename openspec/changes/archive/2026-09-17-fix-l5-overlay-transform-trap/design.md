## Context

渲染实测（Playwright，视口 1440×900）确认的事实，详见 `temps/login-layer-map/`：

| 观察 | 值 |
|---|---|
| `.meeting-doodle` 声明 | `transform: rotate(1.2deg)`（`LoginView.style.css`） |
| `.el-overlay` 实测 | **424×403 @ (822,215)** |
| 注入 `transform: none` 后 `.el-overlay` | **1440×900 @ (0,0)** |
| 登录页根节点 | `.login-page`（**不含** `.wb-shell`） |
| 对话框皮肤来源 | `frontend/src/style.css:65` 全局 `.el-dialog`，取值 `--comp-dialog-*` |
| `--comp-dialog-*` 声明位置 | `tokens.css:293-296`，处于文件顶部 `:root, [data-theme="light"]` 块内（16–549 行） |

约束：`tokens.css:551-556` 登记了口径——模块作用域色板声明在模块根类内，**若弹层 Teleport 到 body，作用域变量会丢失**，此时才允许退化为全局声明。

## Goals / Non-Goals

**Goals**：让登录页错误浮层恢复为真正的阻塞型覆盖层（遮罩覆盖全视口、相对视口居中、点遮罩关闭全页有效），且**不改变**便签卡的手绘倾斜视觉。

**Non-Goals**：不重写浮层组件；不改关闭策略；不把 `.meeting-doodle` 的倾斜改成别种实现（任何 `transform` / `rotate` / `scale` 都会建立同样的包含块，换写法不解决问题）。

## Decisions

**决策：给 `el-dialog` 加 `append-to-body`，让覆盖层 Teleport 到 `body`。**

备选方案与取舍：

| 方案 | 结论 | 理由 |
|---|---|---|
| A. 给 `el-dialog` 加 `append-to-body`（**采用**） | ✅ | Element Plus 对此类场景的标准机制，1 个属性；保留卡片倾斜；皮肤安全（见下）；符合 `frontend-l5-overlay`「覆盖层统一走 EP」口径 |
| B. 删掉 `.meeting-doodle` 的 `transform` | ❌ | 手绘倾斜是登录页设计语言（`frontend-login-hand-drawn-hero`），删样式换功能属破坏视觉；且换用 `rotate` 属性同样会建立包含块，治标不治本 |
| C. 把 `LoginErrorOverlay` 从 `.meeting-doodle__body` 挪到页面根 | ❌ | 改的是 DOM 归属：浮层从「挂载点内」变成「页面根」，会改变 L4/L5 的层级语义与测试定位；且只是把问题挪走，未登记约束 |

**皮肤安全性论证（为什么 A 不会丢皮肤）**：
1. 登录页本来就不在 `.wb-shell` 内，弹层皮肤来自 `style.css` 的**全局** `.el-dialog`；
2. 其取值 `--comp-dialog-*` 声明在 `:root`（16–549 行块内），**不随 Teleport 丢失**；
3. 登录页的模块作用域变量（`--login-rule` / `--login-margin-line` / `--login-dash`）只被页面背景与便签卡边框消费，**弹层不消费**，故 `tokens.css:551` 那条「Teleport 丢作用域变量」的口径在本例不触发。

## Risks / Trade-offs

- [Teleport 后弹层脱离 `.wb-shell` 作用域，未来若有模块作用域皮肤会失效] → 本次已论证登录页不依赖；并在组件注释与 `.meeting-doodle` transform 处登记该约束，避免其他页面照搬时踩坑
- [单测里 `LoginErrorOverlay.spec.ts` 用 `stubs: { teleport: true }` 在树内查找 `.el-dialog`] → 该 stub 让 Teleport 内容仍留在组件树，查找不受影响；且该 spec 现有 3 例失败为既有问题（已用 `git show HEAD:` 版本 A/B 对照证明），本变更不使其恶化
- [遮罩改为全视口后会盖住整页，若未来有人把它当非阻塞提示用会挡交互] → 该组件语义就是错误浮层（阻塞型），且 `frontend-l5-overlay` 已限定非 modal 浮层不按本口径改造

## Migration Plan

无数据迁移。回滚 = 移除 `append-to-body` 属性（同时回滚 `specs/frontend-l5-overlay` 的新增需求）。

## Open Questions

`LoginErrorOverlay.spec.ts` 的 3 例既有失败（`.el-dialog` / `.el-overlay` 在 VTU 中查不到）是否需要在后续变更中一并修掉？本次仅确认与本次改动无关，不顺手改。
