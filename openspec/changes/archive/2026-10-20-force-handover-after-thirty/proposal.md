## Why

执行角色在一步里可以连续推理 30 次仍不交卷。第 31 次框架会强制指定结构化输出工具，但 DeepSeek 开着思考模式时拒绝这种强制调用，整次平台任务被 400 打断。

## What Changes

- 推理轮次上限保持 30。满 30 次后必须停止继续思考和设备操作，只允许提交结构化结果。
- 强制交卷再给 5 次宽限，总上限 35。宽限内仍未交出结构化结果则结束该轮。
- 进入强制交卷时关闭思考模式，避免与强制工具选择冲突。前 30 次仍可思考。
- 执行角色与验收角色同一套轮次规则。

## 关联文档

- PRD-08 AI 助手

## Capabilities

### New Capabilities

### Modified Capabilities

- `agent-sop-runner`: 推理满 30 次后强制交卷并关闭思考，宽限到 35 次

## Impact

- `engines/agents/role/config.py`：轮次与思考开关
- `engines/agents/role/base.py`：强制交卷阶段关闭思考
- 执行与验收的结构化交付口径不变
- 定向测试覆盖轮次边界与强制阶段不带思考
