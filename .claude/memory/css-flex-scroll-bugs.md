---
name: css-flex-scroll-bugs
description: CSS flex 布局中 min-height:0/:deep(*)/固定列宽导致的滚动失效与空白问题 — 诊断 SOP 与修复模式
metadata: 
  node_type: memory
  type: project
  originSessionId: f1410bd3-1472-4dd6-9403-e8f5d0bdfa1f
---

## 三类高频 CSS 布局问题

### 1. `min-height: 0` → 内容截断/无法滚动

**症状**：页面下半部分被截断，无法滚动。DevTools 中 `.doc-body` 的 computed height 被锁死在首屏高度。

**根因**：flex 布局中 `min-height: 0` 表示"允许收缩到零"，父级 `overflow: hidden` 叠加后内容区高度被锁死。

**修复模式**（页面级滚动）：
```css
.doc-page { height: 100%; min-height: 0; overflow-y: auto; }
.doc-body { flex: 0 0 auto; min-height: auto; overflow: visible; }
```

**修复模式**（区域内滚动）：
```css
.outer { overflow: hidden; }
.inner-scroll { flex: 1; min-height: 0; overflow-y: auto; }
```

**排查 SOP**：DevTools → 选中目标元素 → Computed 面板 → 看 `height`/`min-height`/`overflow` 的最终生效值及其来源文件。禁止反复重写模板。

### 2. `:deep(> *)` 通配选择器 → 级联破坏

**症状**：`.main-content :deep(> *)` 意外匹配了底部装饰图、隐藏元素等，导致布局错乱。

**根因**：Vue scoped 的 `:deep(> *)` 匹配**所有**直接子元素，无法区分路由页面和装饰元素。

**修复**：`:deep(> *)` → `:deep(.doc-page)` 限定到具体 class。永远不对通配符使用 `:deep()`。

### 3. 固定像素列宽 → 表格右侧留白

**症状**：表格列宽使用固定 px 值，合计超过容器宽度，右侧出现大片空白。

**修复**：
- 列宽从固定 px 改为百分比（合计 100%）
- `table-layout: fixed` + `width: 100%`
- 容器链全层 `width: 100%`
- 长文本 `text-overflow: ellipsis`

**Why:** 固定列宽无法自适应窗口变化；百分比列宽 + `table-layout: fixed` 可保证列宽比例稳定且表格铺满。
