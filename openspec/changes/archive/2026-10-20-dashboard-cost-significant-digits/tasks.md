## 1. 费用卡片

- [x] 1.1 DeepSeek 费用卡片的累计与「今日」按三位有效数字显示，`1.43860156` 为 `1.44`，0 为 `0`，不用科学计数法。验证：对 `formatSignificant(1.43860156, 3)`、`formatSignificant(0.000113785, 3)`、`formatSignificant(0, 3)` 得到 `1.44`、`0.000114`、`0`。
- [x] 1.2 智能体卡总费用仍显示接口里的 8 位小数字符串。验证：阅读 `frontend/src/modules/dashboard/index.vue` 的 `agent.cost_total`。
