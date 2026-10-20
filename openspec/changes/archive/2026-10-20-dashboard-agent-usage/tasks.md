## 1. 小时用量合计

- [x] 1.1 仪表盘 Token、缓存命中、费用与近 12 日曲线改读小时用量，任务数仍按可见任务计。验证：`python -m pytest tests/api/test_dashboard_agent_usage.py -q` 中累计输入、缓存命中、输出与费用与两条小时记录之和一致。
- [x] 1.2 每个可见智能体返回一份用量，跨角色、跨模型相加，费用为 8 位小数字符串，零用量仍列出。验证：同上测试中执行者与验收者合成 `input_tokens == 1200`、`cost_total == "0.01200000"`，且只出现一条该智能体记录。

## 2. 仪表盘卡片

- [x] 2.1 AI 用量区块在五张卡下方为每个可见智能体展示缓存命中、输入、输出、总费用，费用显示 8 位小数。验证：阅读 `frontend/src/modules/dashboard/index.vue` 的智能体卡与 DeepSeek 费用卡的 `decimals`。
- [x] 2.2 统计响应映射 `ai_usage.agents`。验证：阅读 `useDashboardStats.ts` 的 `agents: raw.ai_usage?.agents ?? []`。
