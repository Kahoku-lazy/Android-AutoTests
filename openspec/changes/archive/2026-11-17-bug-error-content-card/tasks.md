# 任务：「错误内容」改成红色渐变卡片

## 1. 令牌

- [x] 1.1 `shared/styles/tokens.css` 新增 `--comp-bug-error-fill`（135°，`--color-red-69` 18% → 6%）

## 2. 样式

- [x] 2.1 `.bug-detail__body`：填充换 `--comp-bug-error-fill`，描边换 `--app-border-strong`，圆角换 `--app-radius-md`
- [x] 2.2 `.bug-detail__body`：加 `4px 4px 0 0 var(--ink)` 硬偏移影
- [x] 2.3 字号确认仍是 `--app-size-sm`（14）

## 3. 登记

- [x] 3.1 `references/tokens.md` §1.20 记录 `--comp-bug-error-fill`
- [x] 3.2 `references/components/cards.md` §5 记录「错误内容卡」这一已批准偏离

## 4. 验证

- [x] 4.1 实跑 computed：`borderRadius: 6px 10px` · `boxShadow: rgb(30,30,36) 4px 4px 0 0` · `backgroundImage: linear-gradient(135deg, red/0.18, red/0.06)` · `borderColor: ink 24%` · `fontSize: 14px`
- [x] 4.2 `npx vitest run tests/bug-manager` 2 文件 / 11 用例全绿；`npm run lint:styles` 无新增违规
- [x] 4.3 截图核对 `temps/bug-error-card-before-after.png`：卡片与元信息块可区分，正文不被红底抢
