## Context

L5 现状（静态检索基线，见 `报告-前端区域层级与L4-L5现状复盘.html` §四）：13 处 `el-dialog` + 2 处 `el-drawer` 已全部走 Element Plus；违规集中在两类——8 处浏览器原生 `confirm()`（6 文件，全在 workflow）与 4 处自建 backdrop / modal（`LoginErrorOverlay.vue`、`workflow/index.vue` 的 `.wf-modal`、`PageElementsPanel.vue` 的 `.pep-enlarge-mask`、`StructureAnalysisPanel.vue` 的 `.sap-enlarge-mask`）。

可复用的既有资产：`shared/components/patterns/ConfirmButton.vue`（`el-button` / `DoodleBtn` + `ElMessageBox.confirm` 封装）、`style.css` 的 `.el-dialog` / `.el-message` 全局皮肤、`shared/components/StepScreenshotPanel.vue` 已用 `el-dialog` 做图片预览（同类场景的 EP 先例）。

## Goals / Non-Goals

**Goals:**

- 消除 8 处原生 `confirm()` 与 4 处自建 backdrop / modal，使 L5 阻塞层统一由 Element Plus 承载
- 对外契约（组件 props / emits、页面状态、后端调用、路由）保持零破坏
- 不新增共享零件，只用既有 `ElMessageBox` / `el-dialog`

**Non-Goals:**

- 不修 L4 层口径（AppTable 能力边界、分页三套实现、表单校验口径）——另开变更
- 不撰写 L4 / L5 层速查（属文档类变更，非本次范围）
- 不抽共享「图片放大预览」组件（见 Decisions D4）
- 不改造右键菜单、画布 canvas / svg 叠加层、光标锚定 `.el-picker`

## Decisions

**D1 · 8 处 `confirm()` 一律用 `ElMessageBox.confirm`，不用 `ConfirmButton`**

八处全部是命令式处理器（`if (!confirm(...)) return`、键盘 `Delete`、双击连线），其中 `PageFlowVueFlow.vue` 三处根本没有触发按钮；`ConfirmButton` 是按钮组件，只能在按钮位置使用，塞进右键菜单的原生按钮里还会引入同层两套按钮样式。备选：抽一个 confirm composable——属新增零件，被 Non-Goals 排除。

**D2 · `stores/libraryStore.ts` 保留 Element Plus 调用，不反转控制权**

该处是 Pinia store 内的覆盖确认。更干净的方案是 store 返回信号、由调用方确认后重试，但会改动调用方与保存状态机，超出最小改动范围。取舍：状态层依赖 UI 组件被登记为已知取舍（见 Risks），并以 spec 场景钉住取消语义。

**D3 · `LoginErrorOverlay` 改为 `el-dialog` 薄封装，不用 `ElMessageBox.alert`**

现有对外契约是声明式的（`:visible` / `:message` / `@close`，由 `serverError` 驱动）。`el-dialog` 保持 `LoginView.vue` 调用方零改动，同时删掉自建遮罩、手写 ESC 监听与 overlay 过渡 CSS。备选：`ElMessageBox.alert`——需改调用方结构，且与 `clearServerError` 的状态清理耦合更紧。

**D4 · 两处缩略图放大浮层各自改为 `el-dialog`，不抽共享组件**

用户已明确「不需要任何新零件」。两处的详情字段形状不同（元素字段 6 项 vs 结构分区字段 7 项），强行抽出需引入字段描述式配置，属过度设计。取舍：对话框壳仍有两份重复，登记为后续可选收敛项，不在本次处理。

**D5 · 关闭交互一律沿用 EP 默认，保持与改造前一致**

四处原实现都是「点击遮罩关闭」+（`.wf-modal` 另有）ESC 关闭，与 `el-dialog` 的 `close-on-click-modal` / `close-on-press-escape` 默认值一致，因此不额外设置这两个 prop；目录对话框的「打开即聚焦并全选」由 `@opened` 钩子补足（EP 不保证原生 `autofocus` 生效）。

**D6 · 修正本变更作者在前序报告中的归类误差**

`报告-前端区域层级与L4-L5现状复盘.html` §五 把 `ScreenshotView.vue`（`ref` 指向 `<canvas class="overlay">` 边界框绘制层）与 `PageScreenshotOverlay.vue`（在流内 `<svg class="shot-pane__overlay">` 圈选层）误归为「自建浮层」。按实测更正为在流内叠加层，避免后续据此误改。

## 模块防火墙自检

- 跨 App import：不涉及。本变更只改 `frontend/src`，无 Django App 间 import 变化
- 禁止跨 App import service / runner / consumer / state_machine：不涉及
- 所有 INSERT / UPDATE / DELETE 收敛到各 App 的 api.py：不涉及，本变更不新增任何后端写操作
- 前端不直连数据库；仪表盘不做写操作：保持。本变更不改任何 `api.ts` / HTTP 调用
- 新增跨模块依赖：无。`ElMessageBox` 与 `el-dialog` 均为 element-plus 既有全局依赖（`main.ts` 已装配全量样式）

## Risks / Trade-offs

- [原生 `confirm()` 的同步语义变为 Promise，事件处理器需转 async，可能被连点触发两次] → 一律保留 `if (!ok) return` 早退结构；`PageFlowVueFlow.vue` 的 keydown 处理器转 async 后同样早退
- [`libraryStore.ts` 让状态层依赖 UI 组件，单元测试环境需 stub `ElMessageBox`] → 登记为 D2 已知取舍；若既有 store 单测涉及该分支，改为注入式 stub
- [删除自建遮罩 CSS 后模板残留类名或孤儿样式] → 模板与样式同批删除，并以 `rg` 复核类名命中为 0
- [el-dialog 的焦点与滚动锁与 L0 溢出策略交互] → 只用 EP 默认行为、不设 `append-to-body`；改后做浏览器目视回归
- [确认框文案与原 `confirm()` 不完全一致] → 统一 `cancelButtonText: 取消` / `confirmButtonText: 确定` / `type: warning`，提示主体沿用原文案

## Migration Plan

- 无数据迁移，纯前端实现替换；无后端、表结构或配置变更
- 回滚：revert 本变更提交即可，无需补偿操作
- 验证顺序：`npm run typecheck` → `npm run build:check` → `vue-frontend-check` → 浏览器目视（登录错误浮层 / workflow 新建目录 / 两处缩略图放大 / 三处画布删除确认）
