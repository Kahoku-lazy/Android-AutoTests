# 设计：错误内容卡

## Context

`BugDetailDrawer.style.css` 的 `.bug-detail__body` 是等宽 `<pre>`：

```css
background: var(--app-bg-card);              /* 与元信息块、纸面几乎同色 */
border: 1.5px solid var(--app-border-light); /* 近纸色，实际看不见 */
border-radius: var(--app-radius-sm);
/* 无影 */
```

Doodle Craft 的层次靠「页面底 → 卡片 → 浅底内嵌 → 白卡」四层背景 + 硬偏移影拉开，而这块既没有影、描边又不可见，所以贴不回卡片层。

## Goals / Non-Goals

**Goals**：一眼看出「这是一段独立贴出来的错误记录」；红色承载错误语义但不压过 14px 正文；与抽屉里其它块（元信息浅底块、按键）分得开。

**Non-Goals**：不改模板结构、不改数据、不改元信息块与按键；不改列表页的失败条目底色。

## Decisions

### D1 渐变令牌落 T0，浓度 18% → 6%

```css
--comp-bug-error-fill: linear-gradient(
  135deg,
  color-mix(in srgb, var(--color-red-69) 18%, transparent),
  color-mix(in srgb, var(--color-red-69) 6%, transparent)
);
```

- 色相用标记红 `--color-red-69`（主题既有原子），两端 `color-mix` 派生 → 不新增颜色原子，符合"调色板只降不增"。
- 浓度比设备页输入框（45% → 20%）低一档：输入框只托一行字，这里是整段等宽正文，45% 会把字压成"红底黑字"的告警条。
- 终点混 `transparent` 而不是 `--app-bg-card`：混透即"浓度"，换底色不留死色。

### D2 卡片几何复用既有口径

`1.5px solid var(--app-border-strong)`（墨 24%）、`--app-radius-md`（`6px 10px`）、`4px 4px 0 0 var(--ink)` 硬影——与抽屉外框、AppCard 的强调硬影同一套数字，不新造几何。

### D3 正文 14px 不变，层级靠卡片不靠字号

字号已在上一变更收成 14px。本次**不**再调字号：卡片靠"底色 + 描边 + 影"从元信息块里跳出来，字号继续与元信息对齐，避免同一抽屉再出现第三档。

## Risks / Trade-offs

- [红底 + 等宽 14px 长错误栈时色块面积大] → 浓度压到 18%→6%，且卡片有 `max-height: 46vh` 内部滚动，超长内容不会把抽屉撑爆。
- [硬影在滚动容器上可能被裁] → 影在 `<pre>` 自身、不在滚动父级，`overflow: auto` 只裁内容不裁影。

## Migration Plan

纯样式改动 + 一条派生令牌。回退 = `.bug-detail__body` 还原为 `--app-bg-card` 底、`--app-border-light` 边、无影，并删掉令牌与两处登记。

## Open Questions

无（浓度与卡片形制已由需求方在候选图中确认：B · 红 18% → 6%；1.5px 墨边 + 4px 墨色硬影）。
