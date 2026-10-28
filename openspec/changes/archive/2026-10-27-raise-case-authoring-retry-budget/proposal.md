# 提高用例编写重试预算并让验收一次列全阻断

## Why

模块拆分上线后，152 的全量任务已经不再截断，但两次尝试仍失败：首轮验收只列了 2 条阻断，重写修掉后又发现 REQ-024、档位序列等新阻断。`CASE_MAX_ATTEMPTS=2` 只给一次重写，验收又不是穷尽式，导致「修好旧的、冒出新的」，任务很难收敛。

## What Changes

- 每个模块的最大尝试次数从 2 提到 **3**：首稿 + 两次按验收意见定点修复；重写仍附上一版完整文档，只改点名问题。
- 验收 `message` 的问题条数上限从 20 提到 **40**，并要求**首轮一次列全所有阻断**；后一轮不得因为首轮没列而把旧内容当新阻断（首轮未提交的内容除外）。
- 更新 `appliance-case-authoring` 与 `appliance-case-authoring-task` 的尝试次数描述与场景。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `appliance-case-authoring`：单模块最多三次尝试，第三次仍不通过才判失败。
- `appliance-case-authoring-task`：任务失败条件改为模块三次尝试都未通过。

## Impact

- 仅提示词与常量：`engines/agents/workflow/case_authoring_workflow.py`、`engines/agents/prompts/case_verifier_prompt.py`。
- 测试：模块工作流三次尝试单测、验收提示词纪律断言。
- 无数据库、接口、前端变化。
