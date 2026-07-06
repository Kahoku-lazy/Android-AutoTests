---
name: five-phase-workflow-with-review-gates
description: 五阶段流程 + 每阶段审核门禁——探索→审核→规划→审核→拆解→审核→执行→审核→验收
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 921bc6d5-c227-471c-a6f0-467192f54b52
---

用户要求每次任务必须按五阶段执行，每阶段输出后等审核，通过才进入下一阶段。

## 流程

```
收到需求
  │
  ├─ Phase 1: 探索（Explore agent 并行，只读）
  │   └─ 输出: 发现清单（涉及文件、关键代码、潜在问题、需要澄清的点）
  │   └─ ⏸️ 审核门禁: AskUserQuestion 确认理解正确
  │
  ├─ Phase 2: 规划（Plan agent，设计方案）
  │   └─ 输出: 实施计划（改动文件、步骤、风险、验证方式）
  │   └─ ⏸️ 审核门禁: ExitPlanMode 等审批
  │
  ├─ Phase 3: 拆解（TaskCreate，原子化）
  │   └─ 输出: 任务列表（每个任务独立可验证）
  │   └─ ⏸️ 审核门禁: 确认任务粒度合理
  │
  ├─ Phase 4: 执行（逐任务实施）
  │   └─ 每个任务: 编码 → 编译验证 → 测试
  │   └─ ⏸️ 审核门禁: 每个任务完成后输出结果
  │
  └─ Phase 5: 验收（全量回归 + 报告）
      └─ 输出: HTML 报告 + 执行摘要
      └─ ⏸️ 审核门禁: 展示报告、截图、修复日志
```

## 铁律

- 🔴 不得跳过任何审核门禁
- 🔴 探索未完成不得规划
- 🔴 规划未审批不得执行
- 🔴 执行出现 3 次以上编译/语法错误 → 回到规划阶段重新拆解
- 🟠 每个 Phase 的审核门禁必须明确等待用户反馈

## 本次教训

case-manager 任务中跳过了审核门禁：
- 探索后直接写代码 → 选择器错误反复出现
- 规划后未等审批 → 方案多次变更
- 没有拆解步骤 → 一次改太多文件导致定位困难
- 验收时用户发现问题 → 说明审核门禁缺失

**关联**：[[agent-ownership-thinking]] [[task-completion-summary]] [[test-plan-workflow]]
