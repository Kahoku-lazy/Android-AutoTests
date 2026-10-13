## Why

角色费用按 4 位有效数字取位后，很小的缓存命中费用会变成 `5.12e-05` 这种科学计数法，读起来不像金额。需要改成小数点后固定 4 位、四舍五入。

## What Changes

- **BREAKING**：输入、输出、缓存命中三项费用不再保留 4 位有效数字，改为小数点后 4 位、四舍五入。例如 `0.00467` 为 `0.0047`，`0.00463` 为 `0.0046`，`0.0000512` 为 `0.0001`。
- 小于 `0.00005` 元的一项在取位后为 `0`。价目、高峰、假日和「只计未命中输入」的算法不变。
- 平台任务费用仍按原口径，不随这次取位规则改变。

## 关联文档

无关联需求编号。这是在已归档的角色计费能力上改取位规则。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `agent-role-billing`: 三项费用的取位由 4 位有效数字改为小数点后 4 位、四舍五入。

## Impact

- `engines/agents/billing.py`：取位函数。
- `engines/agents/role/base.py`：返回值沿用费用方法的结果，本身不再二次取位。
- 主规格 `agent-role-billing` 中「4 位有效数字」的需求与相关场景。
- 不改 `engines/ai/billing/`、`apps/ai_assistant/deepseek_billing.py`、前端。
