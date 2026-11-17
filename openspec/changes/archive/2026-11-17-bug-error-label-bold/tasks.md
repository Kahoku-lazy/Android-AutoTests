# 任务：错误内容行首标签加粗

## 1. 解析

- [x] 1.1 新增 `helpers/errorDetail.ts::splitErrorDetail`（行首 ≤12 字符 + 中英冒号；排除空白/斜杠；冒号后 `//` 按 URL）
- [x] 1.2 新增单测 `tests/bug-manager/p0/errorDetail.spec.ts`（标签拆分、多行、无标签行、URL、空文本）

## 2. 渲染

- [x] 2.1 `BugDetailDrawer.vue`：`<pre>` 改 `<div>` + 逐行 `<p>`，行首标签 `<span class="bug-detail__line-key">`
- [x] 2.2 `BugDetailDrawer.style.css`：行级 `white-space: pre-wrap`；`.bug-detail__line-key` 取 `--app-font-weight-bold`

## 3. 验证

- [x] 3.1 探针：`lineKey` = 「来源任务：」14px / 700，正文 400，行数 4；卡片仍为红渐变 + 4px 硬影
- [x] 3.2 `npx vitest run tests/bug-manager` 3 文件 / 16 用例全绿；`npm run typecheck` 通过；`npm run lint:styles` 无新增违规
- [x] 3.3 截图核对 `temps/bug-error-label-before-after.png`：字段名与值一眼可分，卡片几何与行距未变
