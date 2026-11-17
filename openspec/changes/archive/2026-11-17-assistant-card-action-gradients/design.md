# 设计：动作键底色改成语义渐变

## Context

`AssistantCard.vue` 一个组件出两种卡：`kind === "assistant"` 是颜料片（`.assistant-card__action` ×2：配置 / 对话，基础样式是透明底 + 1.5px 虚线 + 笔色 hover 浅底）；否则是工作流便签卡（`.sop-card__action--config` 柠黄 85%、`--task` 青绿 78%、第三块是笔色 30% 占位块）。

## Goals / Non-Goals

**Goals**：四枚键底色按语义区分、统一 20%→5% 渐变、视觉语言与表格/状态徽标一致。

**Non-Goals**：不动卡片结构、不动虚线白名单、不动占位块、不动 hover 的位移与阴影几何。

## Decisions

### D1 颜色映射

| 卡 | 动作 | 语义色令牌 |
|---|---|---|
| 助手 | 配置 | `--c-workflow`（天蓝） |
| 助手 | 对话 | `--c-device`（薄荷绿） |
| 工作流 | 配置 | `--c-workflow`（天蓝） |
| 工作流 | 任务 | `--c-element`（薰衣草紫） |

### D2 渐变口径与其它页一致

```css
background: linear-gradient(180deg,
  color-mix(in srgb, var(--c-workflow) 20%, var(--paper)),
  color-mix(in srgb, var(--c-workflow) 5%, var(--paper)));
```

与 BUG 表纸、任务状态徽标同一手法（同一份「20%→5%」约定），审阅时不必重新理解一套。

### D3 hover 只留位移与硬影

原 `.assistant-card__action:hover` 会把底色换成 `--assistant-marker-tint`，那会把渐变冲掉。改为 hover 不动背景，仅 `translate(-1px,-1px)` + `2px 2px` 硬影（沿用笔色硬影）。

### D4 模板加两个修饰类

助手卡的「配置」「对话」原本共用 `.assistant-card__action`，需要 `--config` / `--chat` 两个修饰类才能分色；工作流卡已有 `--config` / `--task`，只换底色。

## Risks / Trade-offs

- [20%→5% 的蓝色与绿色在浅纸底上差异不大] → 两色相相距远（天蓝 vs 薄荷绿），且描边同为虚线墨框；若实看仍接近，可把绿色换 `--app-status-success` 加深。
- [hover 不再换底色，反馈变弱] → 位移 + 硬影仍在，且渐变本身已是浅底。

## Migration Plan

纯样式 + 两个 class。回退 = 还原模板 class 与样式块。

## Open Questions

无。
