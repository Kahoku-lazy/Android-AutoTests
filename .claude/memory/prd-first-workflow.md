---
name: prd-first-workflow
description: 收到功能需求时必须先同步 PRD 文档，再进入技术流程
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b05814f4-5f5d-4bc7-9238-26a81baf151e
---

用户多次强调"先修改需求"意味着先更新 PRD 文档。正确顺序：

```
用户提需求 → 同步 PRD（更新用户故事/功能规格/API端点/版本号）→ 技术方案 → 编码 → 验证
```

禁止：PRD 未同步前开始写代码或出技术方案。禁止：代码写完后才补 PRD。

PRD 文档位置：`dev_docs/02-PRD需求/`。每次更新必须改版本号和变更记录。

**Why:** 2026-07-06 用户明确指正——PRD 是"事前设计"不是"事后记录"。之前对话中 4 个需求（拖拽移动/批量选择/一级目录创建用例/批量移动API）的 PRD 同步放到了代码实现之后，流程顺序错误。

**How to apply:** 收到"做/改/加/修"类功能需求 → 第一步问"PRD 里有没有这一段？"→ 没有就先写 PRD。参照 [[developer-agent]] 的 PRD 先行约束。
