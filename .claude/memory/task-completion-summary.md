---
name: task-completion-summary
description: 每个任务完成后必须输出执行过程摘要，含触发的 Skill/Agent/MCP
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 921bc6d5-c227-471c-a6f0-467192f54b52
---

用户要求：每个任务完成后必须输出执行过程摘要。

**Why:** 让用户清楚地看到任务是怎么完成的——用了哪些工具、走了什么流程、是否有跳步或遗漏。这是对 [[test-plan-workflow]] 的补充约束。

**How to apply:** 每次任务结束时输出如下格式：

```
## 执行过程

| 阶段 | 工具 | 做了什么 |
|------|------|------|
| 代码探索 | Explore agent ×N | ... |
| 规范加载 | xxx Skill | ... |
| 输出 | Write/Edit | ... |

触发过的 Skill：xxx, yyy
触发过的 Agent：Explore ×N, Plan
使用的 MCP：playwright（浏览器截图）, filesystem（文件操作）
```
