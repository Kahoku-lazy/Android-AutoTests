# 设计：设备表字号对齐 BUG 表

## Context

`device-pool` 现在的字号来源分散：表头走全局 `.el-table th`（12px）；正文 14px 由 `DevicePoolView.style.css` 的 `td` 规则给；但胶囊、序列号行、操作键各自写死 12px；型号写死 16px。BUG 表刚统一成「表头 16 / 内容 14 / 时间 12」，设备表要对齐。

## Goals / Non-Goals

**Goals**：三档字号单一来源、表头不折行。

**Non-Goals**：不动列宽（除表头 nowrap）、不动间距、不动结构、不动共享令牌。

## Decisions

### D1 表头 16px 写在本页作用域

设备页此前没有覆写表头字号（沿用全局 12px）。在 `.device-table-wrapper :deep(.el-table th.el-table__cell)` 上加 `font-size: var(--app-size-md)` 与 `white-space: nowrap`，只影响本页。

### D2 型号与序列号行都降到 14px

需求是「其它全部 14」。型号原本 16px 是为了与 BUG 编号对齐，但设备表没有独立「标题」列，型号就是首列主语；按字面统一到 14px，靠字重（heavy）维持层级而不是字阶。若之后想要「首列 16」的两档制，把 `.dev-id__model` 改回 `--app-size-md` 一行即可。

### D3 只有绝对时间留在 12px

「接入 YYYY-MM-DD HH:mm:ss」是辅助时间戳，保留 12px；相对时间（11 分钟前）承担主要信息，保持 14px。

### D4 胶囊与操作键跟随内容档

连接 / 可见性胶囊、状态标签、操作胶囊与「⋯」都从 12px 提到 14px，避免一格里出现两种字号。

## Risks / Trade-offs

- [胶囊放大后 连接/可见性 列可能挤] → 这两列 minWidth 90/110，14px 下仍单行；实测超出再调 `minWidth`。
- [表头 16px 可能撑宽或折行] → 加 `nowrap`；列宽不动，必要时再调。

## Migration Plan

纯样式。回退 = 还原这几处字号声明。

## Open Questions

无。
