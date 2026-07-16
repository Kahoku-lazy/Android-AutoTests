# animal-tabs 内容区超出视口无法滚动（常见问题）

> 状态：✅ 已修复（CaseBreakdown）· 日期：2026-07-13 · 模块：前端 · 标签：**常见问题**
> 影响页面：BUG 问题汇总 / 失败明细（`CaseBreakdown.vue`）、设备管理（`device-pool/index.vue`，已用内层滚动修复）

---

## 现象

- `animal-tabs` 内列表/卡片数据超过一屏后，下半部分被截断
- 鼠标滚轮、触控板均无法继续向下查看
- DevTools 中 Tab 内容区高度被限制在父容器内，子内容溢出不可见

---

## 问题原因

### 1. `.doc-body` 误用 `flex: 1; min-height: 0`（主因）

```css
/* ❌ CaseBreakdown.vue 原写法 */
.doc-body {
  flex: 1;
  min-height: 0;
}
```

在 `App.vue` 中 `.main-content` 已设 `overflow: hidden`，且 `.doc-page` 为 `height: 100%` 的 flex 子项。此时 `.doc-body` 的 `min-height: 0` 表示**允许收缩到零高度**，内容区高度被锁死在首屏，超出部分被裁剪，且无法把高度传递给外层滚动容器。

这与 [报告页滚动失效](./前端-报告页滚动失效.md) 为同一类问题。

### 2. `animal-tabs` 默认 flex 链未释放高度

`animal-island-vue` 的 Tabs 内部结构为：

```
.animal-tabs
  .animal-tabs__list      ← Tab 标签头
  .animal-tabs__content   ← 内容槽
    .animal-tabs__inner   ← 实际插槽内容
```

若未显式设置 `overflow: visible` / `min-height: min-content`，中间层容易在 flex 布局下变成「固定高度 + `overflow: hidden`」，子列表无法撑开页面。

### 3. 两种修复策略（按场景选型）

| 策略 | 适用场景 | 做法 |
|------|----------|------|
| **页面级滚动** | 整页列表（报告、BUG 汇总） | `.doc-page { overflow-y: auto }` + `.doc-body { flex: 0 0 auto; min-height: auto }` + tabs 各层 `overflow: visible` |
| **区域内滚动** | 固定头尾、中间表格（设备管理） | 外层 `overflow: hidden` + 内层 `.table-scroll { flex:1; overflow-y:auto }` |

CaseBreakdown 采用**页面级滚动**（与报告列表 `index.vue` 一致）。

---

## 修复内容（CaseBreakdown.vue）

```css
/* ✅ 页面作为唯一滚动容器 */
.doc-page {
  height: 100%;
  min-height: 0;
  overflow-y: auto;
}

.doc-body {
  flex: 0 0 auto;
  min-height: auto;
  overflow: visible;
}

/* ✅ 放开 tabs 高度约束，让内容撑开 doc-body */
.view-tabs :deep(.animal-tabs__content),
.view-tabs :deep(.animal-tabs__inner) {
  overflow: visible;
}
.view-tabs :deep(.animal-tabs__inner) {
  min-height: min-content;
}
```

---

## 排查 SOP（常见问题速查）

1. **页面区域空白/截断** → DevTools 选中 `.doc-body`、`.animal-tabs__content`，看 `computed height` 与 `overflow`
2. 若 `min-height: 0` + 父级 `overflow: hidden` → 优先改 `.doc-body` 为 `min-height: auto`
3. 若需固定布局内滚动 → 给**内容子节点**设 `flex:1; min-height:0; overflow-y:auto`，不要只改 tabs 外壳
4. 禁止对 `main-content :deep(> *)` 使用通配选择器（见报告页滚动失效文档）

---

## 关联文件

- `frontend/src/modules/report-generator/CaseBreakdown.vue`
- `frontend/src/modules/report-generator/index.vue`（正确参考实现）
- `frontend/src/modules/device-pool/index.vue`（区域内滚动参考）
- `frontend/src/App.vue`（`.main-content` 滚动边界）
