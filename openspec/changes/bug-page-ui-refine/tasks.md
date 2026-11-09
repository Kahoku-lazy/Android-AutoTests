## 1. 结构与皮肤

- [x] 1.1 index.vue：删除「BUG 单 Tickets」标题，FilterTabs 加 ug-category-tabs 类并留在分区头左侧。验证：CDP 截图确认筛选标签在列表区左上。**验证结果**：通过。
- [x] 1.2 index.style.css：分类标签淡色底（runner/ai/case）+ 墨框选中；工具条 padding 改 space-xs / space-md；表格改用 .bug-workbench :deep(...)，表头 14px + 柠檬 22%、表体 12%、悬停 20%。验证：build 23.8s。**验证结果**：通过。

## 2. 门禁与目视

- [x] 2.1 ue-tsc / uild:check / 	ests/bug-manager / lint:lines。验证：全绿。**验证结果**：tsc 0；build 23.8s；虚线 0 处。
- [x] 2.2 真实页面截图（CDP 登录后 /bugs）。验证：	emps/bug-live.png。**验证结果**：通过。
