---
name: agent-must-be-used
description: 创建了专用 agent 的任务必须通过该 agent 执行，禁止手动替代
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 921bc6d5-c227-471c-a6f0-467192f54b52
---

创建了专用 agent 的任务，**必须**通过该 agent 执行，禁止自己手动写代码替代。

**案例**：为「编写测试脚本」创建了 `test-automator` agent，但后续手动写了 `run_tests.py` 的拆分和调试。agent 定义好了却没用，等于白创建。

**Why:** 创建 agent 是为了封装特定领域的知识和工作流。手动替代 = 绕过 agent 的内置约束和最佳实践。

**How to apply:**
1. 创建了 agent → 后续同类任务必须通过 `Agent` 工具调用它
2. 如果 agent 表现不好 → 改进 agent 定义，而不是绕过它
3. 调用方式：`Agent(subagent_type="test-automator", prompt="...")`

**关联**：[[test-plan-workflow]]
