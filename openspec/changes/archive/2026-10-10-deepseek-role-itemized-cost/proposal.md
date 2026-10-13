## Why

角色一轮回复只拿到 token 用量，费用仍被合成一个总数，也无法按法定节假日取消高峰。实验角色需要与用量同样的三项费用，并且只按 DeepSeek 当前两个模型计价。

## What Changes

- DeepSeek 费用只保留 `deepseek-flash` 与 `deepseek-v4-pro`。未登记模型名（含旧名）费用为 0，不再折成 Flash。
- 费用按输入、输出、缓存命中拆开，单位元，各保留 4 位有效数字。输入费用只计缓存未命中部分，缓存命中单独计价。
- 高峰为北京时间周一至周五 9:00–12:00、14:00–18:00，单价为空闲的 2 倍。法定节假日全天按空闲。周末含调休上班日仍按空闲。节假日库未收录的年份退回「只看周一至周五」。
- 角色按提供商匹配计费：DeepSeek 返回上述三项；其它提供商返回 0。
- **BREAKING**：`engines/agents` 不再提供把三项合成一个总数的计费函数，也不再把 `deepseek-chat`、`deepseek-reasoner`、`deepseek-v4-flash`、`deepseek-v4-flash-vision-exp` 按正式模型计价。

## 关联文档

无关联需求编号。这是 `engines/agents` 实验角色的计费，不改平台任务费用。

## Capabilities

### New Capabilities

- `agent-role-billing`: 角色按模型类型，把一轮用量折成输入、输出、缓存命中三项费用（元）。

### Modified Capabilities

（无。平台任务费用与模型目录里「旧名按 Flash 计费」的需求不改。）

## Impact

- `engines/agents/billing.py`：只计算 DeepSeek 当前两个模型的三项费用，并用节假日库取消法定假日高峰。
- `engines/agents/role/base.py`：按提供商匹配计费，返回与用量相同粒度的三项费用。
- `requirements.txt`：新增 `chinesecalendar>=1.11.0`。
- 不改 `engines/ai/billing/`、`apps/ai_assistant/deepseek_billing.py`、前端与任务列表的 `deepseek_cost`。
