## Why

测试报告分区的状态筛选目前借用内容页签（`AppTabs`）承载：四个状态各自复制一份表格，页签挤在分区标题正下方；激活项用深灰紫底配墨色字，对比度不足，整条筛选看上去像一个贴边的黑色色块。筛选条既没有和表格工具栏形成层级，也带来了四份重复 DOM 与内层滚动。

## What Changes

- 状态筛选改用共享 `FilterTabs`，放在「测试报告」分区头右侧；「全部 / 已完成 / 失败 / 已停止」各自带数量角标，数量随当前查询结果实时计算。
- 筛选只作用于**一张**报告表，删除 `AppTabs` 的四个 pane 与重复表格；页面纵向滚动回到 `.doc-body`，不再有页签内层滚动。
- 移除报告页私有的 `.report-tabs` 皮肤覆写，改用共享筛选标签的既定外观（浅底 + 墨框激活态），恢复文字对比度。
- 调整「测试报告」分区头内边距，让标题与筛选条同一行、表格卡独立成块。
- 同步 `report-ai-task-list` 能力，补充「按状态筛选报告行」的行为契约。

## 关联文档

- PRD-平台总需求 §7（观测：测试报告）

## Capabilities

### New Capabilities

### Modified Capabilities

- `report-ai-task-list`: 新增「测试报告工作台按状态筛选」要求——状态筛选条、每项计数、单表过滤

## Impact

- `frontend/src/modules/report-generator/index.vue`：模板与脚本改为 `FilterTabs` + 单表，删除 `AppTabs`
- `frontend/src/modules/report-generator/constants.ts`：状态筛选项注释同步为「计数由页面计算」
- 报告列表接口 `GET /api/reports` 契约不变；无后端与数据模型改动
- 现有报告单测仅覆盖常量与空态文案，不需要改断言
