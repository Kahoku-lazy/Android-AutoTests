# 设计：控制区两处微调

## Context

控制区两行由 `index.vue` 渲染，字号来自 `index.style.css` 与共享 `FilterTabs.vue`：

- `.ops-page-info`（「第 X / Y 页 · 共 N 条」）= `--app-size-xs`（12px）
- `FilterTabs.vue` 的 `.filter-tab` = `--app-size-xs`（12px），是跨 8 个页面复用的共享件
- 同一行的 `el-input`（14px）与 `DoodleBtn`（14px）已是正文档

## Goals / Non-Goals

**Goals**：去掉与第二行重复的账号计数；让第二行四处文字同档 14px。

**Non-Goals**：不动共享 `FilterTabs.vue`（其它 7 处消费方的密度是既定口径）；不动表格内三档字号；不动筛选与分页逻辑。

## Decisions

### D1 计数只留一处

「共 N 个账号」与「共 N 条」是同一个 `total` 的两种写法。第二行的页码文案带分页上下文（第 X / Y 页），信息量更大，保留它、删掉第一行的计数。第一行只剩批量动作，右半边留白也不再被占。

### D2 FilterTabs 用作用域覆盖，不改共享件

```css
.ops-controls :deep(.filter-tab) { font-size: var(--app-size-sm); }
```

共享件保持 12px（报告的密集筛选条、任务清单都用它）。只在运营页控制区这一行提档——与设备页「输入件字号在模块内覆盖」同一做法：**差异写在消费方，不写进共享件**。

### D3 页码文案直接改 14px

`.ops-page-info` 从 `--app-size-xs` 改 `--app-size-sm`。它属于控制区正文，不属于表格里的次级信息（邮箱、绝对时间仍是 12px）。

## Risks / Trade-offs

- [控制区比表格正文更"重"]：14px 与正文同档，但控制区只有一行，不抢表格的视觉重心。
- [FilterTabs 的深链覆盖依赖加载顺序]：`index.style.css` 是组件 scoped 样式，加载在共享件之后；实测计算值 14px（见 tasks 验证项）。

## Migration Plan

纯样式 + 删一个 `<span>`。回退 = 还原两处 CSS 与那一行模板。

## Open Questions

无。
