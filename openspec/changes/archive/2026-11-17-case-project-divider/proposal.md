# 用例管理：新建项目与卡片之间加分区虚线

## Why

`/cases` 项目列表里，「新建项目」按钮与项目卡片之间只有 32px 空白，两者在视觉上连成一片：按钮像是第一张卡片的邻居，而不是「这一页的动作」。需求方要求在此处加一条**虚线**把操作带与内容分开。

## What Changes

- 在「新建项目」操作带与卡片网格 / 空态之间插入共享件 `SectionDivider`（`1.5px dashed`，墨色 38%），只做分区、不可点。
- 间距按「靠近操作带、远离内容」给：操作带下方 8px 到虚线，虚线下方 16px 到卡片。
- 不改卡片、不改按钮、不改空态；虚线用已登记的白名单组件，不在页面里就地写 `dashed`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `case-project-sheet`：新增「项目列表的分区虚线」要求。

## Impact

- 前端 `case-manager`：`ProjectList.vue`（引入 `SectionDivider` + 一处模板节点 + 两条样式）。
- 不动接口、不动卡片组件、不动共享件。
