## 1. 共享 DoodleBtn

- [x] 1.1 新增 `frontend/src/shared/components/DoodleBtn.vue`：`tone` 为 danger（红）/ teal（校验与详情）/ yellow（配置），墨色描边 + 硬阴影，disabled 与 hover 对齐模版；验证：对照 `temps/prototype-doodle-content-cards.html` 按钮行，`prefers-reduced-motion` 下无位移
- [x] 1.2 补 `DoodleBtn` 单测（tone 类名、click、disabled）；验证：vitest 通过

## 2. 共享 DoodleNote

- [x] 2.1 新增 `frontend/src/shared/components/DoodleNote.vue`：`variant="note" | "sticky"`，胶带 deco、accent 硬阴影、sticky 状态底色（ok/run/fail/wait），装饰不拦截点击；验证：note 对齐 deco-card，sticky 对齐 Do/Dont，reduce 时无倾角动画
- [x] 2.2 补 `DoodleNote` 单测（变体类名、装饰存在、插槽内容）；验证：vitest 通过

## 3. AI 助手接入

- [x] 3.1 `AgentRouteCard.vue` 改为薄包装 `DoodleNote variant="note"`，校验=`DoodleBtn` teal、配置=`DoodleBtn` yellow；验证：标题/头像/连通状态与点击行为不变
- [x] 3.2 `TaskBoard.vue` 条目改为 `DoodleNote variant="sticky"`，详情=teal、删除=`ConfirmButton` + danger 外观；验证：六态列表仍分组，详情跳转与删除确认仍可用

## 4. 文档

- [x] 4.1 更新 doodle-craft `references/components.md`：内容卡 note/sticky 与涂鸦按钮规格；验证：与实现一致
- [x] 4.2 更新 `frontend/AGENTS.md` 共享件条目；验证：后续可按同一口径引用

## 5. 门禁

- [x] 5.1 `cd frontend && npm run typecheck`；验证：无本变更引入的新错误
- [x] 5.2 vue-frontend-check 扫本变更文件；验证：无新增硬编码色/布局裁剪违规
- [x] 5.3 目视 AI 助手看板：线路卡 + 任务卡 + 三色按钮；验证：与原型同语言
