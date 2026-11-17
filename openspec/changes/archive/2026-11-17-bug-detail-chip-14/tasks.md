# 任务：分类/状态标签回到 14px

- [x] 1.1 `.bug-badge` / `.bug-status` 字号 → `--app-size-sm`（14）
- [x] 1.2 探针复核：编号 16 · 分类标签 14 · 状态标签 14 · 标题 16 · 小节标题 16 · 元信息 / 正文 14 · 按键 14
- [x] 1.3 `npx vitest run tests/bug-manager` 2 文件 / 11 用例全绿；`npm run lint:styles` 无新增违规（存量仅 AppSidebar G13）
- [x] 1.4 截图核对 `temps/bug-chip-16-vs-14.png`：编号仍是身份行里最重的一件
