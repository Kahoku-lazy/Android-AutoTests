## Context

见 `proposal.md`。11 份规格里的引用形态分三类：

1. **承载页清单**（`frontend-doodle-button` 的「已登记承载页清单」、`frontend-doodle-sketch-table` 的模块色/线型登记）——删掉两个页面即可，清单本身仍成立。
2. **举例型**（路由清单、面包屑举例、弹层举例、截图面板举例）——只是把举例换成仍存在的页面（`/cases`、`/workflow`、`/devices`）。
3. **参照型**（`case-manager-workspace-preview` 说「与元素定位工作台同源」、`frontend-split-pane` 说「两个工作台共用」）——参照物消失了，必须改成自指基线或只留用例管理。

## Goals / Non-Goals

**Goals**：规格库不再出现已删模块的页面与路由，validate 与人工核对都能对上现存页面。

**Non-Goals**：不改共享件实现、不改主题令牌、不为这些规格补新约束。

## Decisions

### D1 逐条 MODIFIED，不整份退役

这些规格的主体约束（硬边几何、表纸皮肤、分栏手柄、分页口径）仍然有效且被其它页面使用，只有举例与登记面变化。因此逐条 MODIFIED 保留原 Requirement 与全部 scenario 名，只改涉事句子。

### D2 参照型改为自指基线

`case-manager-workspace-preview` 原先以元素定位工作台为参照。改为「以用例管理自身既有的左栏目录树与工具栏为基线」，并注明该基线在元素定位退役后不再有跨模块对照对象——避免用另一个不存在的页面做参照。

`frontend-split-pane` 的主体是分栏手柄契约，两个工作台只是使用方举例；改为「用例管理工作台」单方使用，契约不变。

### D3 举例统一替换为现存页面

路由/页面举例一律换成 `devices`、`cases`、`workflow`、`reports` 中仍存在的等价页面，不引入新页面名。

## Risks / Trade-offs

- [举例替换后语义漂移] → 每条只替换涉事名词，scenario 名与断句结构不动；提交前逐份对照「删前/删后」确认其余约束未被改写。
- [漏改某处引用] → 收尾用 `grep` 全 `openspec/specs` 搜 `inspector`、`/elements`、`设备检查器`、`元素定位`，命中只允许出现在本单已知保留处（如历史归档变更）。

## Migration Plan

无数据与代码迁移；仅规格文字。归档时按 delta 合并，不删除任何主规格文件。

## Open Questions

无。
