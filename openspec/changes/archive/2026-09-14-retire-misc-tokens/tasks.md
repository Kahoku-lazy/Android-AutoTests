## 1. 复核

- [x] 1.1 复核 25 个目标令牌全仓出现次数 = 1（仅定义行）、`var()` 消费 = 0；验证：带边界 `名称(?![-a-z0-9])` 全仓扫描逐名输出 x1 且都落在 `tokens.css`；删除后「var() consumers = 0」（唯一残留是 `--font-display`，见 1.4）
- [x] 1.2 复核兄弟令牌仍在用：`--app-overlay`(3) · `--app-footer-yellow-text`(2) · `--app-icon-purple-bg`(3) · `--app-shadow-sm/md/lg`(24/11/13) · `--doodle-ink/bg/radius/shadow`(1/5/1/1)`；验证：批次③ 删除后「non-el defined = 139，dead = 0」
- [x] 1.3 排查动态读取：`var(--${…})` · `getPropertyValue` · `setProperty` 与本批无关；验证：全仓仅 `useSidebarResize.ts:25,30` 写 `--side-w`
- [x] 1.4 确认 `--font-display` 的两处外部出现属各自 `:root`：`hifi-guide.md`（total=5 / definitions=3，值 `'DM Sans'`）· `frontend/public/exec-arch.html`（total=8 / definitions=1，值 `'Nunito'`，且该页 0 处引用 `tokens.css`/`style.css`）；验证：`tokens.css` 内 `--font-display` 计数 = 0

## 2. 删除死令牌与注释残留

- [x] 2.1 删除 `tokens.css` 的 25 行令牌定义；验证：脚本「removed = 25 / 25」(17 行脚本删除 + 8 行随注释块删除)，文件 397 → 300 行
- [x] 2.2 清理注释残留：删 `/* 登录页装饰光晕（仅氛围，非交互色） */` · 删 `/* @deprecated legacy aliases — 统一用 --app-size-*（…）*/` · `阴影/遮罩/光晕` → `阴影/遮罩` · 修正文件头 `@deprecated` 清单（原列 `--app-module-*`、`--app-font-size-*`、`兼容别名块`、`自然背景块`，其中前三项已分别于批次①/③ 删除）；验证：`Select-String '光晕|legacy aliases|--app-module|--app-font-size|--app-glow|--doodle-texture|自然背景'` = 0，双空行扫描 0 命中

## 3. 文档同步

- [x] 3.1 删 `.agents/skills/doodle-craft/references/tokens.md` §1.7 的 `icon` 行（保留 sm/md/lg 三行与「阴影统一扁平投影」说明）；验证：该文件 `--app-icon-shadow` 0 命中
- [x] 3.2 重新同步 `.agents/skills/doodle-craft/SKILL.md:61`：批次① 已删的 `--app-module-*` 说明被外部改写复活，本批再次删除；验证：该句 0 命中（全仓 `--app-module-` 仅存在于已归档变更文档中）

## 4. 门禁与静态验证

- [x] 4.1 运行 `cd frontend && npm run typecheck`；验证：**exit 2，错误集合与前两批完全一致**（`tests/dashboard/p0|p1/*.spec.ts` 20 · `device-inspector/store.ts` 4 · `case-manager/ProjectTree.vue` 3 等共 34 个，均为既有 DTO/类型不匹配）；`tokens.css` 0 提及
- [x] 4.2 构建校验 `npx vite build --mode development`；验证：`✓ built in 1m 48s`，成功
- [x] 4.3 用 `vue-frontend-check` 技能过一遍样式层门禁（calibration §7 全部强制扫描：8 条样式类 + 5 条逻辑/协议类）；验证：命中项均为既有内容（`.empty-state__icon` 64px · 令牌本身 hex/rgba · `--el-*` 阴影与圆角），本变更新增样式声明 = 0；一.1 按静态口径记 ⚠️
- [x] 4.4 P3 收尾统计：重跑全量死令牌扫描，**非 `--el-*` 死令牌 = 0**（139 个存活令牌）；验证：批次① 31 + 批次② 68 + 批次③ 25 = 124 个零消费令牌全部清除（`--el-*` 由 EP 全量样式消费，非死）
