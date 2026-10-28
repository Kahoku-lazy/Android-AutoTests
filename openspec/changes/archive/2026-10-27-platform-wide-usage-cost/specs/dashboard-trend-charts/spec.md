## ADDED Requirements

### Requirement: 仪表盘统计自动刷新

仪表盘在页面可见期间 MUST 每 30 秒静默刷新一次统计数据，刷新 MUST NOT 点亮「刷新」按钮的 loading，也 MUST NOT 让已展示的统计退回加载骨架。页面隐藏（`document.hidden` 为真）时 MUST NOT 发请求；页面重新可见时 MUST 立即刷新一次。组件卸载时 MUST 清理定时器与可见性监听，MUST NOT 在离开页面后继续请求。刷新失败时 MUST 保留上一次成功的数据，MUST NOT 把统计清零。

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
