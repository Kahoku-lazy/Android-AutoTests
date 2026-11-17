## ADDED Requirements

### Requirement: BUG 分布图表

BUG 管理页 SHALL 在「BUG 概览」之下提供「BUG 分布」图表区块，包含两个维度：

- 处理状态环形图：待处理 / 已解决 / 已忽略，圆心显示 BUG 总数；
- 任务类型条形图：UI 自动化 / 用例编写。

图表数据 MUST 直接取自 `GET /api/bugs/` 响应中的 `summary`（`open` / `resolved` / `ignored` / `ui_automation` / `case_authoring` / `total`），MUST NOT 由前端重新统计 `items`，MUST NOT 新增额外接口。图表 MUST 随筛选结果更新（筛选后 `summary` 变化即重绘）。

#### Scenario: 图表随概览一起呈现

- **WHEN** 用户打开 BUG 管理页
- **THEN** 「BUG 概览」KPI 卡下方出现「BUG 分布」区块，左环形图右条形图，两图数据与上方 KPI 卡一致

#### Scenario: 状态与类型维度正确

- **WHEN** `summary` 为 `open=4, resolved=6, ignored=2, ui_automation=5, case_authoring=7, total=12`
- **THEN** 环形图三段分别为 4 / 6 / 2 且圆心显示 12；条形图两行分别为 5 / 7

#### Scenario: 空数据不报错

- **WHEN** 所有统计值为 0
- **THEN** 图表仍渲染坐标与图例，数值全为 0，不出现 `NaN` 或负值

#### Scenario: 图表不重复请求接口

- **WHEN** 页面加载或切换筛选
- **THEN** BUG 数据只由列表接口请求一次，图表复用该响应中的 `summary`
