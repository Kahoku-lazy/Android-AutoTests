## 1. 页面节点上限与顶格反馈

- [x] 1.1 把工作流节点注册表里页面节点的实例上限由 10 改为 50（其余类型不动）。验证：新增 `frontend/tests/workflow/p0/page-node-cap.spec.ts`，断言注册表页面节点上限为 50、第 50 个可建、第 51 个被拒；`cd frontend && npx vitest run tests/workflow/p0/page-node-cap.spec.ts` 通过（实测 6 用例全绿）
- [x] 1.2 「+ 页面」创建失败时把上限原因写到画布工具栏状态行（与「+ 起点」「+ 终点」同形态，不改弹窗/toast）。验证：同一用例挂载画布组件（mock `@vue-flow/core`）连点「+ 页面」至顶格，断言工具栏出现含「50」的提示文案
- [x] 1.3 用同一用例锁定其余三条边界未被改动：起点上限 1、终点上限 5、弹窗不限。验证：用例中三组断言全绿

## 2. 超限存量文档不被截断

- [x] 2.1 用例：向 store 灌入含 60 个页面节点的快照后，断言 60 个节点全部保留、节点计数为 60、删除 1 个后快照仍可保存（不因超限而丢弃或拒绝加载）。验证：`cd frontend && npx vitest run tests/workflow/p0` 全绿（2 文件 13 用例）

## 3. 门禁与实测

- [x] 3.1 前端静态门禁（只跑改动范围）：`npx prettier --check src/modules/workflow tests/workflow/p0/page-node-cap.spec.ts` 全绿 · `npx eslint src/modules/workflow` 0 error（46 条既有 warning）· `npx vue-tsc --noEmit` 0 错误。注：`src/**` 全量 prettier 另有 2 个与本变更无关的未格式化文件（`element-locator/ProjectWorkspace.vue` 属工作区他人在改、`shared/components/WorkbenchHeader.vue`），未纳入本单
- [x] 3.2 浏览器实测（Chromium，平台已在线）：真实资产「H6810设备页面关系流」打开为 11 个节点 → 点「+ 页面」变 12（新节点 n24）→ 删除新增节点并等自动保存后库内回到 11，未残留；另造一篇预置 49 个页面节点的临时流，第 50 个可加、第 51 个被拒且工具栏出现「最多 50 个「页面节点」」，0 控制台报错；临时流已删除。证据：`temps/page-node-cap-browser/assertions.json`（12/12 断言）+ 5 张截图
