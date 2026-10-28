## Context

前端 `usageTokenValue` 原按 <1K 返回原始值，卡片 suffix 带 `token`，副标题带 token 数；用户要求统一单位和精简副标题。

## Decisions

1. 所有 token 展示统一走 `formatUsageToken`：≥1,000,000 用 `M`，否则用 `K`，保留 2 位。
2. 卡片 `value=usageTokenValue`、`suffix=K/M`、`decimals=2`；副标题 `providerText` 只拼接厂商。
3. 明细表与顶部 chip 复用同一格式函数，避免口径分叉。

## Risks

- 10 token 显示 `0.01K`，符合“只用 K/M”的规则。
