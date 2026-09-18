## 1. 共享件扩展

- [x] 1.1 `SkeletonCard.vue` 增加 `variant`（默认 `card`）；`list` 档渲染 `lines` 条等高占位条（高度 20px 为几何量、`row-gap` 取 `--app-space-sm`），保留 `role="status"` + `aria-label="加载中"` + `prefers-reduced-motion` 降级；验证：Chromium 断言 —— 默认档 4 条高度仍为 `60/24/12/24px`，`list` 档 6 条均为 `20px`、`row-gap=8px`
- [x] 1.2 `dashboard/components/StatsCard.vue` 既有用法回归；验证：默认档渲染结果与改动前逐条一致（4 条 + 相同高度），`role` / `aria-label` 保留
- [x] 1.3 `reduced-motion` 降级；验证：Chromium 在 `reducedMotion: reduce` 下 `animation-name` 实测为 `none`，默认下为 `skeleton-shimmer`

## 2. 修假空态（两个项目工作台）

- [x] 2.1 `case-manager/ProjectWorkspace.vue` 解构 `loading` 并在内容之前插入 `<div v-if="loading" class="doc-body"><SkeletonCard variant="list" :lines="6" /></div>`，原错误态降级为 `v-else-if`，内容为 `v-else`；验证：静态核对 —— `loading` 分支偏移 2777 < `SkeletonCard` 2817 < 内容 `v-else` 2986，顺序正确，且页面已解构 `loading`
- [x] 2.2 `element-locator/ProjectWorkspace.vue` 同上；验证：分支顺序 2611 < 2651 < 2817，顺序正确且已解构 `loading`
- [x] 2.3 加载期不再挂载子树 → `ProjectTree` / `LocatorTree` 自带的 `EmptyState` 不会在加载期抢跑；加载完成后 `tree` 仍为空的场景仍渲染空态；验证：两个页面模板均不含自己的 `EmptyState`，空态仍由子树承担（未被绕过）

## 3. 区块骨架统一

- [x] 3.1 替换 6 处裸 `el-skeleton`（`case-manager/ProjectList.vue` ×1、`element-locator/ProjectList.vue` ×1、`element-locator/LocatorFileView.vue` ×1、`element-locator/components/LocatorFilePanel.vue` ×1、`element-locator/components/PageElementsWorkbench.vue` ×1、`workflow/PrototypeList.vue` ×1）为 `SkeletonCard variant="list"`；验证：全仓 `<el-skeleton` 命中数为 **0**
- [x] 3.2 删除模块私有 `__loading` 容器及其死 CSS（`project-list-page__loading` ×2、`proto-list-page__loading`、`page-workbench__loading`）；其中 `PageElementsWorkbench` 的布局容器重命名为 `.page-workbench__state` 以保留弹性布局，其余三处仅有的 `max-width: 720px` 一并删除（已核实其 `.project-grid` / `.proto-grid` 无宽度约束，骨架应与内容同宽，原约束反而不一致）；验证：全仓 `__loading` 命中数为 **0**
- [x] 3.3 保留 12 处 `v-loading`（原地遮罩分层）与 1 处 `WbLoader`（品牌 loader 例外）；验证：`v-loading` 命中数 12 未变、`WbLoader` 2 引用未变

## 4. 错误态调用点统一

- [x] 4.1 `element-locator/components/PageElementsWorkbench.vue` 的 `<el-alert>` + 相邻重试按钮换成 `<ErrorState :message="error" @retry="loadElements" />`；验证：全仓 `<el-alert` 命中数为 **0**，错误态自带重试

## 5. 门禁与验收

- [x] 5.1 `npm run lint:styles` 退出码 0；验证：批 1/2/3 全绿，"场景名/模块名别名" 48 条、"消费位置裸色字面量" 33 处（均未上升）
- [x] 5.2 `npx vite build --mode development` 通过（`built in 33.84s`，退出码 0）；验证：既有 `tests/dashboard/**` / `store.ts` / `ProjectTree.vue` 无关报错未新增（本变更未触碰任何 `.ts`）
- [x] 5.3 Chromium 断言（真实 `tokens.css` + `SkeletonCard.vue` 的 style 块 + 复刻标记）：**9 项全 PASS** —— 默认档 4 条 `60/24/12/24px`、`list` 档 6 条 `20px` 且 `row-gap 8px`、两档均有 `role="status"` + `aria-label`、默认动画为 `skeleton-shimmer`、`reduced-motion` 下为 `none`。**限制**：契约级验证，未加载真实运行的应用与数据
- [x] 5.4 三态口径静态复核：`SkeletonCard` 19 引用 / 10 文件、`EmptyState` 48 / 19、`ErrorState` 48 / 24；骨架实现仅剩共享件自身（`shimmer` 命中全部落在 `SkeletonCard.vue` 内）；两个工作台加载分支顺序正确且已解构 `loading`
- [x] 5.5 `git diff --name-only` 本变更部分为 11 个文件（1 个共享件 + 6 个骨架替换 + 2 个工作台 + 页面元素工作台含错误态），与 `proposal.md` 的 Impact 段一致；工作区其余改动属变更 1–5 与其他在飞工作，未触碰