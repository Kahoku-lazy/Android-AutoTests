## 1. 复核

- [x] 1.1 复核 31 个目标令牌在 `frontend/src` + `frontend/tests` 中 `var()` 消费为 0，且同段 6 个（`--app-green`/`--app-blue`/`--app-accent-blue`/`--app-accent-purple`/`--app-ink`/`--app-ink-muted`）仍有消费；验证：扫描 239 个 `.vue/.css/.ts/.js` 文件 → 「dead tokens with consumers = 0 / 31」；实测在用计数 `--app-green`=1 · `--app-blue`=1 · `--app-accent-blue`=1 · `--app-accent-purple`=11 · `--app-ink`=20 · `--app-ink-muted`=71
- [x] 1.2 排查 `getPropertyValue` / `setProperty` 等非 `var()` 读取路径，确认与本批 31 个令牌无关；验证：全仓仅 `shared/composables/useSidebarResize.ts:25,30` 的 `setProperty('--side-w')`（写入且不在本批），无 `getPropertyValue`

## 2. 删除死令牌

- [x] 2.1 删除 `tokens.css` 的 `--app-module-*` 段（1 行注释 + 8 个令牌）；验证：改名全仓检索 0 命中（`frontend/src` 0 · `.agents` 0 · `dev_docs` 0）
- [x] 2.2 收缩 `@deprecated 旧色` 段：删除 23 个死令牌，保留 6 个在用令牌；验证：31 名全仓 `var()` 消费 0；保留的 6 个仍定义在 `tokens.css:228,229,230,231,233,234` 且消费计数非 0

## 3. 文档同步

- [x] 3.1 删除 `.agents/skills/doodle-craft/SKILL.md` 第 61 行关于 `--app-module-*` 的说明；验证：`.agents` 下 31 名检索仅剩 `html-report/references/PROMPT.md:62` 的 `--text-secondary`（该 skill 自带 `:root` 同名定义，与本批无关）

## 4. 门禁与静态验证

- [x] 4.1 运行 `cd frontend && npm run typecheck`；验证：**exit 2，但 34 个错误全部落在本变更未触碰的文件**（`tests/dashboard/p0|p1/*.spec.ts` 20 个、`src/modules/device-inspector/store.ts` 4 个、`src/modules/case-manager/components/ProjectTree.vue` 3 个，另 7 个同族）——均为 workspace 内其它在建改动引起的既有 DTO/类型不匹配；`tokens.css` 在日志中 0 提及 → 非本变更引入
- [x] 4.2 构建校验 `npx vite build --mode development`；验证：`✓ built in 2m 3s`，成功（CSS 与产物无报错）
- [x] 4.3 用 `vue-frontend-check` 技能过一遍前端门禁（样式层）；验证：已跑 calibration §7 全部强制扫描（8 条样式类 + 5 条逻辑/协议类）于变更范围 `tokens.css`，三块输出见变更归档说明；逐项记录中一.1 记 `⚠️`（静态口径，diff 内无布局声明变动）
- [x] 4.4 静态复核：对 31 个删除名做全仓检索，确认 0 命中（`frontend/src` 0 · `dev_docs` 0）；验证：`dev_docs` 0 命中 → 三份现状复盘报告无需同步（本次删除项在文档中从未被提及）
