## ADDED Requirements

### Requirement: 任务详情页按需渲染轮次

任务详情页 MUST 默认只展开第一个用例，其余用例保持折叠；用户展开用例时才渲染其轮次。单个用例内的轮次 MUST 分页展示，每页 20 条，并显示「第 X / Y 页」与上一页 / 下一页控件。用例卡 MUST 带 `content-visibility: auto`，滚动到视口外的用例不参与布局与绘制。前端 MUST 按 `round_ids` 从 `data.rounds` 取轮次，MUST NOT 复制整份轮次对象。打开一个 12 用例、156 轮、8,640 条事件项的任务时，页面 DOM 节点 MUST 少于 3,000。

#### Scenario: 默认只展开第一个用例

- **WHEN** 打开一个含 12 个用例的任务详情
- **THEN** 只有第一个用例的轮次可见，其余 11 个用例为折叠态

#### Scenario: 轮次分页每页 20 条

- **WHEN** 展开一个含 60 轮的用例
- **THEN** 首屏只渲染 20 条轮次，并显示「第 1 / 3 页」
- **AND** 翻到第 2 页后渲染第 21–40 条

#### Scenario: 大任务 DOM 规模受控

- **WHEN** 打开任务 142（12 用例、156 轮、8,640 条事件项）并等待首屏稳定
- **THEN** `document.querySelectorAll('*').length` 小于 3,000

#### Scenario: 轮次顺序与接口一致

- **WHEN** 展开任一用例
- **THEN** 页面上的轮次顺序与该用例 `round_ids` 的顺序一致
