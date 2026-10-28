## Why

仪表盘模型用量的 token 目前混用原始数字、K 与 `token` 文案，卡片副标题同时显示厂商和 token，视觉不统一。用户要求 token 单位统一为 `M`/`K`，卡片下标只保留厂商名。

## What Changes

- 分类卡片 token 只使用 `M` 或 `K`（保留 2 位小数）；不再出现原始 token 或 `token` 后缀。
- 分类卡片副标题只显示 `DeepSeek` / `DASHSCOPE`，不再带 token 数。
- 最近明细表 token 列、顶部累计 chip 同样使用 `M`/`K`。

## Capabilities

### Modified Capabilities

- `model-usage-ledger`: 调整仪表盘展示单位与副标题。

## Impact

- 仅前端展示；后端字段与账本不变。
