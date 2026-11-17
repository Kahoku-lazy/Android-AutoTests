# 设计：状态徽标用 CSS 变量驱动七态

## Context

`TaskBoard.vue` 的 `.status-pill` 目前只有 `.is-success` 与 `.is-failed/.is-interrupted` 两条着色规则，其余四个 tone（`pending` / `running` / `paused` / `cancelled`）落到无彩默认样式。`taskStatusTone()` 已经把状态归并成这七个 tone，模板只输出 `is-<tone>` 类名。

## Goals / Non-Goals

**Goals**：七态可分、底色渐变、文字可读、零新令牌。

**Non-Goals**：不改 `taskStatusTone` 归并口径、不动分组与筛选、不动统计图、不改筛选下拉。

## Decisions

### D1 用一个 CSS 变量 `--sp-color` 承载状态色

每态只声明 `--sp-color`，`.status-pill` 基类统一消费它生成渐变、描边与文字色。这样新增状态只需加一行变量，不必复制三段样式。

```css
.status-pill {
  --sp-color: var(--app-border-strong); /* 兜底：未知状态仍可读 */
  border: 1.5px solid color-mix(in srgb, var(--sp-color) 75%, transparent);
  background: linear-gradient(180deg,
    color-mix(in srgb, var(--sp-color) 20%, var(--app-bg-card)),
    color-mix(in srgb, var(--sp-color) 5%, var(--app-bg-card)));
  color: color-mix(in srgb, var(--sp-color) 70%, var(--ink));
}
```

### D2 七态色相全部取自既有令牌

| tone | 令牌 | 观感 |
|---|---|---|
| pending | `--c-dashboard` | 柠黄 |
| running | `--c-workflow` | 天蓝 |
| paused | `--app-status-purple` | 紫 |
| success | `--app-status-success` | 绿 |
| failed | `--app-status-danger` | 红 |
| interrupted | `--c-ops` | 赭橙 |
| cancelled | `--c-report` | 灰紫 |

不新增令牌，符合 G11（颜色原子只降不增）。

### D3 文字用「状态色 70% + 墨色」而不是现成的浅色状态文字令牌

`--app-status-*-text` 是给浅底纯色块准备的；渐变底只有 5%~20% 的浓度，配这些文字会偏淡。混墨后得到同色相的深色，既保留色相又保证对比度（>4.5:1）。

## Risks / Trade-offs

- [赭橙 `--c-ops` 与柠黄 `--c-dashboard` 在小尺寸下相近] → 两者亮度差异明显，且描边同为各自色相；实测徽标已带文字标签，色相只作辅助。
- [渐变在 1px 高差内不明显] → 徽标高度约 20px，20%→5% 的落差可辨；与表纸渐变同一手法，观感统一。

## Migration Plan

纯样式。回退 = 还原 `.status-pill` 样式块。

## Open Questions

无。
