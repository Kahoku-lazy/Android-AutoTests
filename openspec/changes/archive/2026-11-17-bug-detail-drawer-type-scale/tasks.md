# 任务：BUG 单详情抽屉字号两档

## 1. 样式

- [x] 1.1 `.bug-detail__no` → `--app-size-md`（16）
- [x] 1.2 `.bug-badge` / `.bug-status` → `--app-size-md`（16）
- [x] 1.3 `.bug-detail__title` → `--app-size-md`（16，原 24）
- [x] 1.4 `.bug-detail__subtitle` → `--app-size-md`（16）
- [x] 1.5 `.bug-detail__body` → `--app-size-sm`（14，原 12）
- [x] 1.6 `.bug-meta` 与按键不动（14）

## 2. 验证

- [x] 2.1 实跑探针：抽屉标题 16 · 编号 16 · 分类标签 16 · 状态标签 16 · 单据标题 16 · 小节标题 16；元信息 / 任务链接 / 错误正文 14；按键 14
- [x] 2.2 `npx vitest run tests/bug-manager` 2 文件 / 11 用例全绿；`npm run lint:styles` 无新增违规（存量仅 AppSidebar 的 G13）
- [x] 2.3 截图核对 `temps/bug-drawer-before-after.png`：头部行、标题、小节标题同档；正文不再小于元信息块
