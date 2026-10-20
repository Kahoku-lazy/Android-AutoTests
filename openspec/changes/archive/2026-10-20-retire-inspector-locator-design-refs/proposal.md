## Why

`retire-inspector-and-element-locator` 已删除设备检查器与元素定位两个模块，但视觉与布局类的 11 份规格仍把它们当「举例 / 承载页」写在要求里（如硬边按键承载页清单、SketchTable 模块色登记、分栏台两个工作台、面包屑举例、路由清单）。规格现在描述的是不存在的页面，后来人按规格核对会找不到对象。

## What Changes

- 从 11 份规格的对应要求里删掉「设备检查器」「元素定位」及其路由（`/inspector`、`/elements/*`）的举例与承载登记，其余约束（几何、配色、分栏、分页、面包屑结构）保持不变。
- 不新增任何行为要求；不改变共享件与主题的实际实现（本单只改规格文字与必要的举例，代码已在上一单落地）。

## 关联文档

无 PRD 编号：承接 `retire-inspector-and-element-locator`（2026-10-20 归档）的收尾。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `frontend-doodle-button`: 硬边按键「已登记承载页清单」去掉设备检查器与元素定位文件详情页
- `frontend-doodle-sketch-table`: 模块色与描边线型登记去掉设备检查器与元素定位
- `frontend-doodle-subpage-nav`: 单页模块举例与面包屑举例去掉两模块
- `frontend-doodle-sketch-card`: 三处列表使用 SketchCard 的举例去掉元素定位
- `frontend-split-pane`: 两个工作台改为只含用例管理
- `case-manager-workspace-preview`: 「与元素定位工作台同源」的参照改为自身基线
- `frontend-l0-design-tokens`: 截图面板与元素选择浮层的举例去掉
- `frontend-l2-page-region`: 路由举例去掉 `/inspector`、`/elements/*`
- `frontend-l3-container`: 页面举例去掉两模块
- `frontend-l4-data-surface`: 设备检查器表格分页举例去掉
- `frontend-l5-overlay`: 「保存到元素定位」弹层举例去掉

## Impact

- 仅规格：`openspec/specs/` 上述 11 份。
- 不改代码、不改数据库、不改接口。
