## 1. 令牌登记

- [x] 1.1 在 `frontend/src/shared/styles/tokens.css` 的 `--size-border-width` 旁新增 `--size-stroke-sketch: 2.5px`，并在其上注释其用途（手绘描边宽度，与工作台实线边框 3px 区分）；验证：全仓仅此一处声明该原子，`cd frontend && npm run lint:styles` 的批 2（token 唯一性与引用完整性）通过
- [x] 1.2 确认新增原子名符合 `--size-*` 规格命名且不含模块前缀；验证：`npm run lint:styles` 批 2 不含新命中

## 2. 登录页样式收敛

- [x] 2.1 在 `views/LoginView.style.css` 的 `.login-page` 作用域内声明 `--login-line: dashed` 与 `--login-border: var(--size-stroke-sketch) var(--login-line) var(--ink)`，删除 `--login-dash: var(--comp-sidebar-dash)`；验证：该文件对 `--comp-sidebar-dash` 的引用命中为 0，页面计算值 `--login-line: dashed`
- [x] 2.2 把 `.hero-cta` 的 `border: 2.5px solid var(--ink)` 改为引用 `var(--size-stroke-sketch)`；`.hero-cta--ghost` 的 `border-style: dashed` 改为 `var(--login-line)`；`.meeting-doodle` 的 `border: var(--login-dash)` 改为 `var(--login-border)`；验证：文件中不再出现 `2.5px` 描边字面量，浏览器 computed `border-style` 仍为 `dashed`
- [x] 2.3 在 `views/styles/auth-form-card.css` 中把 `.form-submit .el-button` 的 `border: 2.5px solid var(--ink)` 改为引用 `var(--size-stroke-sketch)`；把 `margin: -var(--app-space-sm) 0 0 28px` 改为 `margin: calc(-1 * var(--app-space-sm)) 0 0 28px`；验证：浏览器 computed `margin-top` 为 `-8px`（改前为 `0px`，说明非法声明此前被丢弃）

## 3. 验证

- [x] 3.1 运行 `cd frontend && npm run lint:styles`，四批检查全部通过且无新增命中
- [x] 3.2 运行 `cd frontend && npx vue-tsc --noEmit`：本次改动仅 `.css`，不产生类型影响；命令唯一的报错来自 `tests/ai-assistant/p0/useTaskPublish.spec.ts` 对 `ATTACH_ACCEPT` 的引用，属工作区既有的 AI 助手在途改动，与本单无关
- [x] 3.3 在 1440×900 与 480×900 两个视口截图对比 `/login` 改动前后：描边宽度、线型、描边色、阴影计算值一致；唯一差异是两行校验提示各恢复 8px 上移，Meeting doodle 高度减少 16px 并随垂直居中重新分布（1440 顶边 +8px、480 顶边 +12px）
- [x] 3.4 按 spec 场景「共享线型变化不波及登录页」临时把 `--comp-sidebar-dash` 的值改为实线，确认登录页 Meeting doodle 与「注册」次按钮仍为 `dashed`，随后还原该文件；验证：还原后 `git diff` 在该行无改动
