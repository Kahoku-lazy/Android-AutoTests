## Why

`UiAutoWorkflow.show` 把事件流翻译成控制台时间线，但同一文件里的 `AgentEventsShow` 是一份未接入、且当前无法运行的拆分草稿：方法签名对不上，用量分支的 `else` 会把几乎每条事件都再打一遍。两份逻辑并存，后续改打印格式时不知道以哪份为准。

## What Changes

- 以现有 `UiAutoWorkflow.show` 的打印文案为唯一真相，把分派收进无状态的 `AgentEventsShow.show(event, buf)`。
- 各阶段方法处理完返回是否已消费；只有全部未命中时才打印类型名。
- `UiAutoWorkflow.show` 改为委托 `AgentEventsShow.show`。`run` 仍由调用方持有 `buf`。
- 补一条单测，用假事件锁定现有控制台文本。
- **Non-goals**：不改 `dump`、`run`、`AgentSOPWorkflow`、`__main__`；不改打印文案、截断长度和 `ReplyStart` 清空缓冲的时机。

## 关联文档

无关联需求编号。这是调试用控制台时间线的结构整理，不改变平台对外能力。按 schema 约定，纯重构在 `.openspec.yaml` 设 `skip_specs: true`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。控制台时间线的可见文本与现有 `UiAutoWorkflow.show` 保持一致，不新增或修改需求级行为。

## Impact

- 代码：`engines/agents/workflow/ui_auto_workflow.py` 中的 `AgentEventsShow` 与 `UiAutoWorkflow.show`。
- 测试：新增 `tests/graybox/unit/` 下一条定向单测，不跑 SOP、不连设备。
- 不改前端、接口、数据库，也不改 `engines/ai/**`。
