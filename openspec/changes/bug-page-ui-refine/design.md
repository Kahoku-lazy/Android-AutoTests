## Context

- BUG 页根类 .bug-workbench；列表区结构：分区头（标题 + FilterTabs）→ 筛选条 → 行数/页码 → AppTable。
- AppTable 把 class 合并到内层 el-table，该元素不带页面 scope 属性，.bug-table[data-v] 选择器匹配不到（与报告页同一坑）。

## Decisions

### 1. 与报告页同一套皮肤

表头 14px/700 + 柠檬黄 22%、表体 12%、悬停 20%；分类标签 30px 淡色底 + 墨框选中；工具条上下 4px 等距。两页视觉一致，后续抽共享皮肤时也只需处理一处。

### 2. 作用域锚在页面根

所有表格规则写成 .bug-workbench :deep(...)，不再依赖 .bug-table[data-v]。

## Risks

- [柠檬黄底与 BUG 类别的粉紫/青绿标签对比] → 标签本身有墨框与浅底，仍可分辨。
