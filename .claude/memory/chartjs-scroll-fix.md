---
name: chartjs-scroll-fix
description: Chart.js responsive:true + CSS width:100% 导致横向滚动失效 — 固定 canvas 像素宽 + responsive:false 修复模式
metadata: 
  node_type: memory
  type: project
  originSessionId: f1410bd3-1472-4dd6-9403-e8f5d0bdfa1f
---

## Chart.js 横向滚动失效

**症状**：图表 range 选「一月」（30 天），canvas 的 `scrollWidth === clientWidth`，横向滚动条不出现。或卡片被 canvas 撑到 3000+px 宽。

**根因**（两层）：
1. Chart.js `responsive: true` 按父容器可见宽度重算 canvas 尺寸，即使 JS 已设 `width: 30 * dayWidth`，仍被缩回视口宽度
2. CSS Grid 子项默认 `min-width: auto`，按内容最小宽度（canvas 像素宽）撑开卡片，而非把溢出交给 `.chart-scroll` 滚动

**修复模式**：

```js
// JS: 固定 canvas 像素宽 + 关闭响应式
const CHART_VISIBLE_DAYS = 5
const dayW = scrollEl.clientWidth / CHART_VISIBLE_DAYS
canvas.style.width = `${n * dayW}px`  // 显式像素宽
canvas.width = Math.round(n * dayW * dpr)  // 物理像素
{ responsive: false, maintainAspectRatio: false }
```

```css
/* CSS: Grid 子项限宽 + 仅内部滚动 */
.chart-row { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
.chart-card { min-width: 0; max-width: 100%; overflow: hidden; }
.chart-scroll { overflow-x: auto; }
.chart-inner { flex-shrink: 0; }
/* 移除所有 canvas { width: 100% !important } */
```

**排查 SOP**：
1. 选 range 后检查 `scrollWidth > clientWidth`（应为 ~6 倍）
2. `scrollWidth === clientWidth` → 查 `responsive: true` 或 canvas CSS width
3. 卡片宽度等于 canvas 总宽 → 查 Grid `min-width: 0` / `minmax(0, 1fr)`
4. 默认滚到最右侧是预期（最近数据）；看历史需向左滑

**How to apply:** 涉及 Chart.js + 横向滚动的图表时，必须关闭 `responsive`，手动计算 canvas 像素宽，CSS Grid 用 `minmax(0, 1fr)` 限制卡片列宽。
