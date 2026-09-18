## 1. 复核

- [x] 1.1 复核 68 个目标令牌在 241 个文件（`frontend/src` + `tests` + `index.html`）中 `var()` 消费为 0；验证：精确计数脚本输出「var() consumers remaining = 0」（68 名逐个精确匹配）
- [x] 1.2 复核 4 个在用兄弟令牌仍有消费：`--case-border-subtle`(3) · `--case-border`(1) · `--ai-hint-orange`(3) · `--app-stat-text`(1)；验证：计数非 0；`--app-stat-text` 的消费点是 `views/components/AnimalFace.vue:124 --af-ink: var(--app-stat-text)`，`--af-ink` 在该组件内被 20+ 处 SVG 引用
- [x] 1.3 传递性分析：确认 `--ai-bg-success` / `--ai-bg-error` 的「elsewhere 消费 = 0、唯一引用为同批删除的别名行」；验证：in-file alias 扫描仅命中这 2 个（`tokens.css:138` `--ai-hint-green-bg: var(--ai-bg-success)` · `:140` `--ai-hint-red-bg: var(--ai-bg-error)`）
- [x] 1.4 排查动态读取：`var(--${…})` · `getPropertyValue` · `setProperty` 均与本批无关；验证：全仓仅 `useSidebarResize.ts:25,30` 写 `--side-w`

## 2. 删除死令牌

- [x] 2.1 删除 `tokens.css` 的 68 行令牌定义（`--ai-*` 18 · `--case-*` 38 · `--app-stat-*` 12，含 2 个传递性死亡）；验证：脚本输出「removed = 68 / 68，missing = 空，397 → 329 行」；复核「var() 消费 = 0」且「src/.agents/dev_docs 文本出现 = 0」；4 个兄弟令牌仍在（`tokens.css:125,152,153,156`）

## 3. 文档同步

- [x] 3.1 删 `.agents/skills/doodle-craft/references/tokens.md` §1.11 表的 11 行死令牌行（保留 `--app-stat-text` 行与 section 标题）；验证：脚本输出「rows removed = 11」，该文件尾部只剩 `--app-stat-text` 一行 + 表头，且 68 名在该文件 0 命中

## 4. 门禁与静态验证

- [x] 4.1 运行 `cd frontend && npm run typecheck`；验证：**exit 2，但错误集合与批次②前完全一致且全在未触碰文件**（`tests/dashboard/p0|p1/*.spec.ts` 20 · `src/modules/device-inspector/store.ts` 4 · `src/modules/case-manager/components/ProjectTree.vue` 3 等，共 34 个）；`tokens.css` 在日志中 0 提及 → 既有 DTO/类型不匹配，非本变更引入
- [x] 4.2 构建校验 `npx vite build --mode development`；验证：`✓ built in 1m 53s`，成功
- [x] 4.3 用 `vue-frontend-check` 技能过一遍样式层门禁（calibration §7 全部强制扫描：8 条样式类 + 5 条逻辑/协议类）；验证：命中项均为既有内容（`.empty-state__icon` 64px 字号 · 令牌本身的 hex/rgba 定义 · `--el-*` 阴影与圆角），本变更为纯删除、新增声明 = 0；一.1 按静态口径记 ⚠️
- [x] 4.4 静态复核：68 名在 `frontend`（排除 node_modules/dist）· `.agents` · `dev_docs` 的文本出现 = 0（仅本次 OpenSpec 变更文档中提及）；验证：`tokens.css` 净删除 68 行、`tokens.md` 删除 11 行，diff 中无新增样式声明
