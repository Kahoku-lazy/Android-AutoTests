## 1. 对话区高度（P0）

- [x] 1.1 `ModelDebugPage.vue`：消息列表与空态两种状态共用 `md-chat-body` class（`v-if/v-else` 同时只渲染其一），滚动归属唯一。验证：消息多时有消息、消息少时无消息两种状态下容器高度一致。
- [x] 1.2 `ModelDebugPage.style.css`：新增 `.md-chat-body { height: 132vh; overflow-y: auto }`（原 66vh 上限的两倍）；`.md-msgs` 去掉 `max-height` / `overflow-y`。验证：样式源断言通过，文件内已无 `max-height: 66vh`。
- [x] 1.3 输入区不受影响：`.md-chat-input` 仍在消息区之下、清空 / 发送常驻。验证：发送 / 清空 / 二次确认等对话用例全部继续通过。

## 2. 工具分组折叠（P0）

- [x] 2.1 `ModelDebugPage.vue`：新增 `openToolGroups` 白名单状态与 `toggleToolGroup` / `isToolGroupOpen`；组头由 `p` 改为 `button.md-group-sub--toggle`，带 `aria-expanded` 与 `.md-caret`；工具清单 `v-if="isToolGroupOpen(...)"`。验证：默认不渲染工具条目，点击后渲染（用例 2 条）。
- [x] 2.2 `watch(role)` 中清空 `openToolGroups`，切换角色回到全部收起。验证：新增用例「切换角色后工具分组回到全部收起」通过（测试侧把路由参数 mock 改为响应式以驱动切换）。
- [x] 2.3 `ModelDebugPage.style.css`：`.md-group-sub--toggle` 按钮复位与 hover 态，取值全部走既有令牌（`--app-space-xs` / `--ink` / `--app-highlight`），与页内既有折叠头同一套观感。验证：新增声明只用到既有令牌，无新增裸色值 / 裸字号。

## 3. 测试

- [x] 3.1 改测 `frontend/tests/ai-assistant/p0/useModelDebug.spec.ts`：`mountLoaded` 等待条件由工具名改为角色带；「工具按分类分组」用例改为先展开再断言计数与只读 / 已停用徽标。验证：`npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts` 通过。
- [x] 3.2 新增折叠用例：默认全部收起、点击组头展开该组、逐组独立且可再收起、切换角色后重置。验证：同一命令通过（29 用例全绿）。
- [x] 3.3 版式用例改口径：断言 `.md-chat-body` 为 `132vh` 且承担 `overflow-y`，旧 `66vh` 上限已消失。验证：同一命令通过。

## 4. 门禁与复验

- [x] 4.1 只跑与改动相关的最小集：`npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts`（29 用例）通过；`node tests/check-style-gates.mjs` 目前**停在批 2 硬门禁**，失败项为 2 处 `--font-body` 未声明——来自并行的字体令牌改动（`tokens.css` 第 165 行把字体族声明拆成两行，门禁按单行解析），与本变更的两个文件无关（本次新增声明未引用该令牌）。验证：告警原文与归属已核对。
- [ ] 4.2 用户侧目视复验：刷新验收模型调试页，确认对话区纵向约为原来两倍、工具分类默认收起且可逐组展开。验证：用户确认。
