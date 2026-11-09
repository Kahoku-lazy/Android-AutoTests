## Why

BUG 单页与刚改完的测试报告页是同一类列表页，但两页的列表区结构不一致：BUG 页仍有「BUG 单 Tickets」分区标题、筛选标签是白色胶囊、工具条上下距离不等、表头 12px 且无底色。需求方要求「BUG 单也和测试报告一样的设计」。

## What Changes

- 去掉列表区左上角的「BUG 单 Tickets」标题，分类筛选标签移到该行左侧。
- 分类筛选标签：淡色底（全部=桃粉、UI 自动化=粉紫、用例编写=青绿）+ 墨框选中 + 淡投影，30px 高。
- 工具条（显示行数 / 页码 / 翻页）上下等距 4px，整体上移。
- 表格：表头 14px 加粗 + 柠檬黄 22% 底，表体 12% 柠檬黄，悬停 20%；选择器锚定 .bug-workbench，避免 .bug-table[data-v] 匹配不到的问题。

## Capabilities

### New Capabilities

无（仅视觉与布局收敛）。

### Modified Capabilities

无。

## Impact

- 前端：modules/bug-manager/{index.vue,index.style.css}。
- 后端 / 接口：无。
