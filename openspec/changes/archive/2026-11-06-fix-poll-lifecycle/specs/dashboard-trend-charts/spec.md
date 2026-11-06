## MODIFIED Requirements

### Requirement: 仪表盘统计自动刷新

仪表盘在页面可见期间 MUST 每 30 秒静默刷新一次统计数据，刷新 MUST NOT 点亮「刷新」按钮的 loading，也 MUST NOT 让已展示的统计退回加载骨架。页面隐藏（`document.hidden` 为真）时 MUST NOT 发请求；页面重新可见时 MUST 立即刷新一次。离开仪表盘路由时 MUST 立即停止轮询并清理定时器与可见性监听，MUST NOT 在离开后继续请求；该判定 MUST NOT 依赖组件卸载（页面可能被 keep-alive 缓存而未卸载）。重新进入仪表盘时 MUST 恢复轮询并立即静默刷新一次。刷新失败时 MUST 保留上一次成功的数据，MUST NOT 把统计清零。

#### Scenario: 停留页面自动跟进用量

- **WHEN** 用户停留在仪表盘，且一次任务在页面打开之后产生新的 token 与费用
- **THEN** 最迟 30 秒后「今日 Token 与费用」出现新的点与金额，无需手动点击「刷新」

#### Scenario: 页面隐藏时暂停

- **WHEN** 仪表盘所在标签页被切到后台超过 30 秒
- **THEN** 期间不发起统计请求

#### Scenario: 回到页面立即刷新

- **WHEN** 标签页从后台切回仪表盘
- **THEN** 立即发起一次统计请求，不等待下一个 30 秒周期

#### Scenario: 卸载后不再请求

- **WHEN** 用户离开仪表盘路由
- **THEN** 轮询定时器被清理，之后不再发起统计请求

#### Scenario: 离开路由后不再请求（含 keep-alive 缓存）

- **WHEN** 用户离开仪表盘路由，而该页面被 keep-alive 缓存、组件并未卸载
- **THEN** 30 秒内不再出现 `GET /api/dashboard/stats/` 与 `GET /api/dashboard/activities/` 请求
- **AND** 缓存页不进入错误态，已展示的统计不被清零

#### Scenario: 重新进入仪表盘立即补拉

- **WHEN** 用户从其它页面回到仪表盘
- **THEN** 立即静默刷新一次，不等待下一个 30 秒周期
- **AND** 不出现加载骨架、不点亮「刷新」按钮的 loading
