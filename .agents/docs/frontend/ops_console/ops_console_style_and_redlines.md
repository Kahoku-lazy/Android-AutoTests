# ops-console · 样式与红线

> 归属模块：`frontend/src/modules/ops-console` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/src/modules/ops-console/index.style.css`、`components/OpsUserDrawer.vue`、`frontend/src/shared/styles/tokens.css`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

## 样式

- 模块色 `--c-ops`（赭橙），表格强调色用 `accent="var(--c-ops)"`。
- 抽屉内容被 teleport 到 body：页面级 scoped 样式到不了，身份标签与状态样式由抽屉自己持有（与 serial-log 面板同一口径）。
- 字号、颜色、间距、圆角只用 `shared/styles/tokens.css` 的令牌。

## 红线

- **禁止**在页面里直接改本地状态冒充已保存：动作一律打接口，用响应回带的行替换。
- **允许**本页批量停用；**允许**仅超管的批量注销，且确认文案必须写明历史保留、不可恢复。
- **禁止**跨页全选、按创建者清扫业务数据，以及运营看到或调用批量注销。
- **禁止**把一次性密码写进日志、`localStorage` 或 URL；只在抽屉里显示，关闭即清空。
- **禁止**自己拼身份判定（如 `username === "admin"`），一律读 `useAuthUser`。

## 快速验证

```bash
cd frontend
npx vitest run tests/ops-console
npm run typecheck
npm run lint:styles
```
