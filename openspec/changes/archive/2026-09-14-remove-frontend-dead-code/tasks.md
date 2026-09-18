## 1. 删除前复核

- [x] 1.1 运行 `rg -n "GroupTreePanel" frontend` 与 `rg -n "soft-icon" frontend`，确认除自身文件、`style.css` 与 `frontend/AGENTS.md` 的说明外 0 命中；验证：两条输出与预期一致，若出现真实消费方则停止本变更

## 2. 删除死代码

- [x] 2.1 删除 `frontend/src/shared/components/GroupTreePanel.vue`；验证：`rg -n "GroupTreePanel" frontend` 0 命中
- [x] 2.2 删除 `frontend/src/style.css` 中 `.soft-icon*` 家族（8 组规则，含段落注释）；验证：`rg -n "soft-icon" frontend/src` 0 命中，且 `git diff -- frontend/src/style.css` 只包含该段删除

## 3. 文档同步

- [x] 3.1 更新 `frontend/AGENTS.md` L2 速查 §⑥「已知缺口」：移除 `.soft-icon*` 一条（同段其它条目保持不动）；验证：文档不再声称 `.soft-icon*` 存在

## 4. 门禁与验收

- [x] 4.1 运行 `cd frontend && npm run typecheck`；验证：无本变更引入的新错误（既有无关报错需注明）
- [x] 4.2 构建校验（`npm run build:check`，不可用则 `npx vite build --mode development`）；验证：构建成功
- [x] 4.3 用 `vue-frontend-check` 技能过一遍前端门禁（布局裁剪 / 字号 / 硬编码色 / 契约）；验证：逐项记录，无新增违规
- [x] 4.4 目视抽查 device-inspector、element-locator、dashboard 三页；验证：**验证方式已替代**（用户 2026-09-14 授权按静态等价关单）—— 本环境无可用登录态浏览器，改以「两处删除项全仓 0 消费方」+ 应用启动截图（登录页渲染正常）+ 构建通过作为等价证据；三页浏览器目视**未执行**，风险判定为 0
