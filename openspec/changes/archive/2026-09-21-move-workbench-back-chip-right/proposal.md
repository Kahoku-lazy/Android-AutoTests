## Why

元素定位项目工作台等 L2 子页把「返回项目列表」芯片画在面包屑条左侧，与波浪祖先链挤在一起，主区右上角空着。用户要求该返回芯片放到面包屑条右上角，面包屑仍靠左，一眼能找到回退入口。

## What Changes

- 共享件 `WorkbenchCrumbs` 在同时渲染波浪面包屑与返回芯片时，返回芯片 MUST 靠该条右端（`.doc-body` 顶部导航行的右上角），祖先链 MUST 仍靠左。
- 返回芯片仍留在 `.wb-crumbs` / `.doc-body` 顶部；SHALL NOT 迁入 `.wb-header` 的 `#actions`。
- 路由、`backTo` / `backLabel` / `items` 语义、点击回退行为不变。
- 所有当前传入 `backTo` 的消费页（元素定位、用例管理、报告详情链、AI 深链等）随共享件一起对齐，不在单页再写一套偏移。

## 关联文档

无单独 PRD/ARCH 编号：本变更为既有 L2 子页导航零件的横向排布调整，不新增业务能力。主契约见 `frontend-doodle-subpage-nav`、`frontend-l2-page-region`。

## Capabilities

### New Capabilities

- （无）本变更不引入新能力。

### Modified Capabilities

- `frontend-doodle-subpage-nav`: 返回芯片与波浪面包屑并存时的横向位置：芯片靠 `.wb-crumbs` 右端，祖先链靠左。

## Impact

- 前端共享件：`frontend/src/shared/components/WorkbenchCrumbs.vue`
- 消费页无需改 props；视觉随共享件变化（含 locator `ProjectWorkspace` 上用户点选的「← 返回项目列表」）
- 测试：`frontend/tests/shared/p0/WorkbenchCrumbs.spec.ts` 增加布局断言
- 后端 API、路由、数据契约不变
