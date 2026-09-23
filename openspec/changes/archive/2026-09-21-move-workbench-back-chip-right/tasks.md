## 1. 共享件排布

- [x] 1.1 调整 `WorkbenchCrumbs.vue`：模板先渲染 `.wb-crumbs__list`、后渲染 `.wb-crumbs__back`；芯片 `margin-left: auto`。验证：源码中芯片节点在列表之后，且芯片样式含 `margin-left: auto`。
- [x] 1.2 在 `WorkbenchCrumbs.spec.ts` 增加断言：同时有 `backTo` 与 `items` 时，`.wb-crumbs__back` 在 `.wb-crumbs__list` 之后；仅有 `backTo` 时芯片仍存在且源码含靠右样式。验证：`cd frontend && npx vitest run tests/shared/p0/WorkbenchCrumbs.spec.ts` 通过。

## 2. 门禁

- [x] 2.1 确认消费页未把返回芯片放进 `.wb-header`，且 locator `ProjectWorkspace` 仍用共享件 `back-label="返回项目列表"`。验证：Grep `wb-crumbs__back` 仅出现在 `WorkbenchCrumbs.vue` 与其单测。
- [x] 2.2 跑前端校验：`cd frontend && npm run build` 通过。
