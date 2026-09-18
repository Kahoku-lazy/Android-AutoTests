## 1. 令牌与 L0 纸面

- [x] 1.1 在 `frontend/src/shared/styles/tokens.css` 将 `--paper` / `--doodle-bg` 收敛为原型暖白（`#fffef5` 或极近值）；验证：令牌值与 `temps/hand-drawn-doodle-sidebar.html` 纸色一致
- [x] 1.2 修改 `frontend/src/style.css` 的 L0 `body` 背景：去掉点阵 `radial-gradient`，改为纯 `var(--paper)`；验证：任意页面视口无点阵
- [x] 1.3 修改 `frontend/src/App.vue` 中 `.app-shell` 背景为统一纸色令牌；验证：壳层与 L0 无黄灰断层

## 2. 去掉工作台双纹理

- [x] 2.1 去掉 `frontend/src/style.css` 里 `.doc-page--fixed .doc-body` 的点阵背景，改为透明或纯纸色；验证：固定视口工作台不再出现双层点阵

## 3. 主区涂鸦层

- [x] 3.1 新增 `frontend/src/shared/components/PaperDoodles.vue`，从 temps `.bg-doodles` 复制 SVG，设置 `pointer-events: none`；验证：单独渲染可见稀疏涂鸦且不拦截点击
- [x] 3.2 在 `App.vue` 的 `.main-content` 内挂载 `PaperDoodles`（仅 `showSidebar === true`），内容层 `z-index` 高于涂鸦层；验证：带侧栏页主区有涂鸦、侧栏无；登录页无涂鸦层
- [x] 3.3 为 `.main-content` 提供定位上下文并让涂鸦绝对铺满；验证：涂鸦不随内容滚，且现有内层滚动/`overflow` 策略不变

## 4. 文档同步

- [x] 4.1 更新 `frontend/AGENTS.md` L0 纸面描述（实色纸 + 主区涂鸦）；验证：文档与实现一致
- [x] 4.2 更新 `.agents/skills/doodle-craft/references/layout.md` §4.2；验证：规则改为「暖白纸面 + 主区稀疏涂鸦；禁止点阵/横线本作为全站背景」

## 5. 目视验收

- [x] 5.1 本地目视登录页、仪表盘、至少一个 `.doc-page--fixed` 工作台页，并跑 `cd frontend && npm run typecheck`；验证：纸色暖白、主区有涂鸦、侧栏干净、点击正常、无双滚动条，typecheck 通过
  - 备注：`npm run typecheck` 仍有既有失败（case-manager ProjectTree、device-inspector store、dashboard 测试类型），与本变更文件无关；本变更未引入新的 typecheck 报错
