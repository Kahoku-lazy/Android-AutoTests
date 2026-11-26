## Context

`ProjectSheet.vue` 的编辑状态分两处：

- `dirtyIds`：表格里被「应用改动」过、尚未写库的行；`dirtyCount` 只用于控制「未保存 N 处」chip 与「保存」按钮的可用态。
- `SheetRowDrawer.vue` 的 `draft`：抽屉内正在编辑的草稿，`cloneRow(props.row)` 得来；它只在抽屉内存在，父组件只在「应用改动」那一刻才看到它。

现状的出口全是静默的：`SheetRowDrawer.close()` 直接 `emit("update:modelValue", false)`；`ProjectSheet.vue` 没有任何 `onBeforeRouteLeave` 或 `beforeunload`（全仓也只有 `useTableDragScroll` / `SplitHandle` 用 `onBeforeUnmount` 做清理）。因此抽屉里写的内容在「未应用」阶段完全不受保护，而「已应用未保存」阶段只靠一个 chip 提示。

规格侧现有口径（`openspec/specs/case-project-sheet/spec.md`）已明确「面板内的修改 MUST 先落在草稿中」「在用户点击页面「保存」之前不发出任何写请求」，本次不改这两条，只补「丢弃 / 离开」这一侧的约束。

## Goals / Non-Goals

**Goals:**

- 只要存在未写库的改动（表格标记 ∪ 抽屉草稿），刷新 / 关标签 / 站内跳转 / 关抽屉都 MUST 先拦一次。
- 没有未保存改动时，行为与现状一致，不产生多余弹窗。
- 拦截判定必须是「真实差异」，不能因为打开抽屉、clone 出等价草稿就误报。

**Non-Goals:**

- 不改两段式保存模型：「应用改动」仍不写库，页级「保存」仍是唯一写入口（自动保存属另一条改动线）。
- 不解决抽屉打开时「保存」按钮被抽屉遮住的问题（版式问题，另议）。
- 不动后端、接口、步骤表；不做「草稿本地暂存 / 草稿恢复」。
- 不改其他模块的离开行为。

## Decisions

1. **脏信号取并集：`dirtyCount > 0 || 抽屉草稿与当前行有差异`。**
   只盯 `dirtyIds` 会漏掉用户这次的真实场景（在抽屉里写步骤、还没点应用就刷新）。抽屉侧用 `hasDraftChanges(row, draft)` 判定：两边都过 `editablePayload()` 后做深比较，天然忽略 `step.id` / `updated_at` 这类只读字段，也让「只多了尾部空格」不被当成改动（保存时本来就会 trim）。

   - 备选：在抽屉里每次输入就 `dirtyIds.add`——会把「打开抽屉看一眼」也标成未保存，误报太多。

2. **三层拦截各管一段，互不替代。**

   - `beforeunload`：唯一能拦住刷新与关标签的机制；有脏时 `preventDefault()` + `returnValue = ""`。文案由浏览器决定，不追求定制。
   - `onBeforeRouteLeave`：站内跳转（返回项目列表、面包屑、侧边栏）走应用内确认框，可写清「离开后会丢失」；取消返回 `false` 留在原页。
   - `el-drawer` 的 `before-close`：✕ / 遮罩 / Esc 三条关闭路径都会经过它；footer 的「取消」按钮是自己 `emit` 的，不走 `before-close`，所以同一个确认函数在 `close()` 里复用一次。

   三者共用一个 `useUnsavedGuard(isDirty)`，`isDirty` 传函数而不是布尔值，避免组合式函数持有会过期的快照。

3. **退出登录的确认放在侧边栏、且在吊销会话之前；路由守卫对 `/login` 不再二次拦截。**
   先试过「先导航、后吊销」：`AppSidebar.logout()` 先 `router.push("/login")`，守卫拦下后取消即什么都不做。实测走不通——带 token 访问 `/login` 会被全局守卫改道 `/dashboard`，于是 `onBeforeRouteLeave` 又为 `/dashboard` 弹一次确认，登出永远走不完（探针日志：`leaving -> /login` → `confirm resolved` → `leaving -> /dashboard` → 再弹）。最终方案：

   - 新增 `shared/composables/useUnsavedChanges.ts` 做全局登记（`useUnsavedGuard` 内部自动登记、卸载自动撤销），暴露 `hasUnsavedChanges()`；
   - `AppSidebar.logout()` 在发登出请求前用 `hasUnsavedChanges()` 判断并弹确认，`runLogout` 保持「确认 → 吊销 → 清本地会话 → 回登录页」，取消时三项都不做；
   - 守卫对 `/login` 直接放行（`UNSAVED_GUARD_SKIP_PATHS`），避免侧边栏确认后又被拦一次；这条同时也覆盖 401 强制跳登录——会话已死时再问「要不要留下」没有意义。

   备选（否）：让页面自己的守卫在跳 `/login` 时也弹确认——会出现「两个确认框、第一个确认白点」的死循环。

4. **`beforeunload` 处理器必须判别「本页是否仍是当前路由」。**
   `App.vue` 的 `<router-view>` 外面包着 `<keep-alive :max="5">`，页面被缓存时不会触发 `onBeforeUnmount`，监听器会一直挂在 window 上。因此 `useUnsavedGuard(isDirty, isActive)` 用 `route.fullPath === 页面自己的 fullPath` 作为 `isActive`，避免在别的页面刷新时被一个缓存中的旧页面拦下来。

5. **确认框文案与按钮收进常量文件。**
   离开页与丢草稿的文案在 `modules/case-manager/constants.ts`（`UNSAVED_LEAVE_*` / `DISCARD_DRAFT_*`），退出登录的文案在 `shared/helpers/logout.ts`（`LOGOUT_UNSAVED_*`，按钮用「退出登录 / 留下」）。避免「确定 / 取消」读不出后果。

6. **抽屉把脏状态上抛给页面，而不是页面自己再算一遍。**
   `SheetRowDrawer` 用 `watch(hasEdits, ...)` 发出 `dirty-change`，父组件只存一个 `drawerDirty` 布尔；抽屉关闭时草稿清空，`hasEdits` 自然变 false，脏标记自动回落，不需要额外清理路径。

7. **测试只守分支与顺序，不测 DOM 位置。**
   按 `tests/AGENTS.md` 口径不新增 `tests/` 灰盒用例（本改动纯前端、无接口）；vitest 侧覆盖：`hasDraftChanges` 的等价/差异样例、守卫的「不脏放行 / 确认后放行 / 取消留下 / 跳登录放行 / 缓存页不拦」、全局登记的登记与撤销，以及 `runLogout` 的「无脏不确认 / 脏则先确认 / 取消什么都不做 / 吊销失败仍清本地」。

## 模块防火墙自检

- 依赖方向：只动 `frontend/src/modules/case-manager/`，复用 `@/shared/components`（`DoodleBtn` / `EmptyState`）与 `element-plus` 的 `ElMessageBox`；新增的 `shared/composables/useUnsavedChanges.ts`、`shared/helpers/logout.ts` 只被用例表页面与 `AppSidebar` 使用，不反向依赖任何业务模块。
- 写库路径：不新增任何请求；「保存」仍是唯一写入口，本轮 `api.ts` 零改动。登出请求的端点与载荷不变，唯一变化是「先确认、后吊销」。
- 组件职责：`SheetRowDrawer.vue` 只做「有无差异 → 是否发事件 / 是否弹确认」，差异算法在 `helpers/sheet.ts`，离开守卫在 `composables/useUnsavedGuard.ts`，全局登记在 `shared/composables/useUnsavedChanges.ts`，登出顺序在 `shared/helpers/logout.ts`。
- 无新增自定义异常类，未改 `engines/`，未改依赖边界与计费口径。
- 行数：`ProjectSheet.vue` 271 → 约 288 行、`SheetRowDrawer.vue` 296 → 约 329 行，均在 500 行硬线以内。

## Risks / Trade-offs

- [浏览器原生 `beforeunload` 文案不可定制] → 只承诺「会拦」，说明文案统一写在站内确认框；在 tasks 里记录这是浏览器行为而非缺陷。
- [`beforeunload` 在移动端与部分内嵌浏览器上可能被忽略] → 站内路由守卫与抽屉确认仍有效，且真正写库的「保存」按钮不受影响。
- [登出改为先导航后吊销，503-retry 分支行为变化] → 旧实现在 503-retry 时留在原页并保留登录；新实现此时已在登录页，只能提示后清本地会话。代价可接受：这是服务端异常的少数场景，且本地清会话不会留下半登录状态。
- [401 拦截器的自动跳登录也会经过守卫] → 会话已失效时若页面有脏数据，仍会弹一次确认；选择「留下」只能保住页面内容（无法保存）。属已知边界，记录在 tasks 中待后续用「强制跳转」通道区分。
- [误报：打开抽屉随手改一个字再关，会多一次确认] → 判定用 `editablePayload` 后深比较，回到原值即不算改动；这点代价换来的是不再静默丢数据。
- [守卫依赖组件在路由内挂载] → `ProjectSheet` 是路由页，`onBeforeRouteLeave` 可用；若将来被包进 `KeepAlive` 需要重新评估，写进 tasks 的备注。
