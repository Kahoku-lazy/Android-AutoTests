## 1. 死样式资产

- [x] 1.1 确认 `modules/ai-assistant/ChatView.css` 路径引用 = 0、`--chat-*` 消费 = 0；验证：脚本输出 `chatview_path_refs=0 chatview_var_refs=0`
- [x] 1.2 隔离到 `temps/quarantine/ChatView.css`；验证：文件不再位于 `frontend/src`，且隔离副本存在

## 2. 共享样式命名唯一

- [x] 2.1 `views/shared/` → `views/styles/`（2 份 css）；验证：`views_shared_left=0 views_styles=2`
- [x] 2.2 同步 5 处 `@import` 路径；验证：`views/shared/` 旧路径命中 = 0

## 3. 令牌兜底字面量

- [x] 3.1 确认 `--app-marker-red` / `--c-case` / `--c-workflow` / `--app-offline` 均存在；验证：脚本 `unresolved=0`
- [x] 3.2 `DoodleNote.vue` 7 处 `var(--x, #字面量)` → `var(--x)`；验证：该文件兜底字面量命中 = 0

## 4. 回归与关单

- [x] 4.1 `npm run lint:styles` 通过；验证：exit 0（T0 声明 394 · 颜色原子 198 · 复合值 3）
- [x] 4.2 裸值复核 + 类型检查；验证：`hex_bare=0` · `rgba_bare=0` · `TOTAL_ERRORS=34` · `APP_CODE_ERRORS=0`（与基线一致）
- [x] 4.3 `openspec validate clean-style-asset-hygiene --strict` 通过并归档

## 关单记录（2026-09-15）

| 验证项 | 结果 |
|---|---|
| 死文件引用 | `chatview_path_refs=0` · `chatview_var_refs=0` → 已隔离到 `temps/quarantine/` |
| 目录改名 | `views_shared_left=0` · `views_styles=2` · 旧路径命中 0 · 5 处 `@import` 已更新 |
| 兜底清理 | `DoodleNote.vue` 7 处移除，`unresolved=0` |
| 门禁 | `npm run lint:styles` exit 0 |
| 裸值 / 类型 | `hex_bare=0` · `rgba_bare=0` · `TOTAL_ERRORS=34` · `APP_CODE_ERRORS=0` |
| 构建 | `npm run build` **未执行**（沙箱 `spawn EPERM`）；浏览器核验未做 |
| 未完成项 | 管道溯源（400+ 处）· 23 处跨仓兜底 · `workflow/index.vue` 非 scoped 理由注释 → 登记为 C-2 |