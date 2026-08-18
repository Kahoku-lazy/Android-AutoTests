# Workflow Manifest 规范

适用场景: auto-dev 编排器在执行任何任务时，创建和更新 `plans/{task-slug}/workflow-manifest.json`。

## JSON Schema

```json
{
  "task": "string (kebab-case slug)",
  "created": "ISO8601 datetime",
  "intensity": "lite | standard | strict",
  "stages": {
    "intake": {
      "status": "done | failed",
      "files": "number (涉及文件数)",
      "confidence": "high | medium | low",
      "explored_at": "ISO8601"
    },
    "plan": {
      "doc": "string (方案文件路径)",
      "status": "pending_approval | approved | rejected",
      "approved_at": "ISO8601"
    },
    "code": {
      "files": ["string (修改的文件路径)"],
      "lines_changed": "number",
      "compile_passed": "boolean",
      "status": "done | failed | skipped"
    },
    "review": {
      "report": "string (HTML 报告路径)",
      "p0": "number",
      "p1": "number",
      "p2": "number",
      "status": "done | blocked_by_p0"
    },
    "test": {
      "report": "string (HTML 报告路径)",
      "env": "full | partial | unavailable",
      "passed": "number",
      "failed": "number",
      "skipped": "number",
      "status": "done | partial | skipped"
    }
  },
  "delivery": {
    "report": "string (最终报告路径)",
    "completed": "ISO8601"
  }
}
```

## 上游依赖矩阵

| 当前阶段 | 必须满足的前置条件 |
|---------|------------------|
| `plan` | `intake.status == "done"` |
| `code` | `plan.status == "approved"` |
| `review` | `code.status == "done" AND code.compile_passed == true` |
| `test` | `review.status == "done"` (Lite可跳过) |
| `delivery` | 所有执行过的阶段 `status ∈ {done, skipped}` |

## 操作规则

1. 进入任何阶段前，先校验上游阶段是否就绪
2. 阶段完成后再写入 manifest，不提前写
3. 只更新当前阶段字段，不覆盖其他阶段
4. manifest 更新本身不触发 git commit
5. Lite 模式可跳过 `review` 的 HTML 报告和 `test` 阶段

## task-slug 生成规则

从用户需求文本中提取关键词，转为 kebab-case:
- "给 agent_factory 加 try/except" → `agent-factory-add-try-except`
- "修复 dashboard 统计概览的 loading 问题" → `dashboard-stats-loading-fix`
- "新增批量删除 Agent 功能" → `ai-agent-batch-delete`

## 文件落盘位置

```
plans/
└── {task-slug}/
    ├── workflow-manifest.json
    └── plan.md              (Phase 1 方案文档)
```
