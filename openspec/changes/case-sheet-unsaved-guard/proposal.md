## Why

用例表的编辑是两段式：抽屉里的修改先落草稿，「应用改动」只把草稿塞回表格并标「未保存」，真正写库要再点页面的「保存」。这套模型没有任何离开前拦截——刷新、关标签、点返回项目列表、点侧边栏、甚至抽屉点 ✕ 丢弃草稿，都是静默丢弃。

2026-11-25 现场事故：用户在抽屉里写好步骤后刷新页面，回来只剩新建行时写入的占位步骤；库里 `TC-20261125-0001` / `0002` 的 `updated_at` 等于 `created_at`、步骤表最大 id 就是创建时那两行，证明整条保存链路一次都没发出。草稿态在服务端没有任何残留，属于不可恢复的数据丢失。

## What Changes

- 抽屉里存在未应用的草稿改动时，关闭抽屉（✕ / 遮罩 / Esc / 取消）MUST 先弹确认，取消则留在抽屉里继续编辑。
- 页面存在未保存改动（表格里被标记未保存的行，或抽屉里未应用的草稿）时：
  - 浏览器刷新 / 关闭标签 MUST 触发浏览器原生离开确认；
  - 站内路由离开（返回项目列表、面包屑、侧边栏跳转、侧边栏「退出」）MUST 先弹确认，取消则留在当前页。
- 侧边栏「退出登录」在吊销会话前先确认（读取全局未保存登记），取消时保持登录且页面数据不动；跳转登录页不再二次拦截。
- 无未保存改动时，离开行为与现状逐字一致，MUST NOT 多出任何一次弹窗。
- 退出语义只加提示，不改两段式保存模型本身（「应用改动」仍不写库）。

## 关联文档

无 PRD 条目：本改动来自 2026-11-25 现场数据丢失（用例 `TC-20261125-0001` 步骤回滚到占位文本）的排障结论，属缺陷修复，对应既有规格 `case-project-sheet`「用例行编辑经独立面板」的补充约束。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `case-project-sheet`: 「用例行编辑经独立面板」补充两条硬约束——抽屉丢弃草稿前必须确认、页面带有未保存改动时离开必须提示；并改写「取消抽屉不改行」场景，明确关闭前先确认。

## Impact

- 前端：新增 `frontend/src/modules/case-manager/composables/useUnsavedGuard.ts`（`beforeunload` + `onBeforeRouteLeave` 守卫）、`frontend/src/modules/case-manager/constants.ts`（提示文案常量）、`frontend/src/shared/composables/useUnsavedChanges.ts`（全局未保存登记）与 `frontend/src/shared/helpers/logout.ts`（登出顺序，可测）；改 `helpers/sheet.ts`（草稿差异判定）、`components/SheetRowDrawer.vue`（`before-close` 确认、草稿脏标记上抛）、`ProjectSheet.vue`（接脏标记并挂守卫）、`shared/components/AppSidebar.vue`（退出登录改为先确认、后吊销）。
- 后端 / 接口 / 数据：不改。不新增端点，不写库，不动步骤表；登出端点与载荷不变，只是调用前多一次确认。
- 测试：`frontend/tests/case-manager/p1/sheet.spec.ts` 补草稿差异用例，新增 `frontend/tests/case-manager/p0/unsaved-guard.spec.ts` 守住守卫分支，新增 `frontend/tests/shared/p0/logout.spec.ts` 与 `frontend/tests/shared/p0/unsaved-changes.spec.ts` 守住登出顺序与全局登记。
- 风险边界：`beforeunload` 的提示文案由浏览器决定（各浏览器不可定制），只保证「会拦」；站内离开的确认框是应用内弹窗，可定制文案与按钮。
