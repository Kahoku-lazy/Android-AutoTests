## Context

<!-- 当前状态与约束（只写方案需要的）。动机见 proposal.md - Why，不要重复。 -->

## Goals / Non-Goals

**Goals:**
<!-- 本设计要实现什么 -->

**Non-Goals:**
<!-- 明确排除什么 -->

## Decisions

<!-- 关键技术决策 + 理由 + 考虑过的备选方案 -->

## 模块防火墙自检

<!-- 必填：逐条确认本设计不触碰红线（规则见 AGENTS.md / .claude/rules/api-conventions.md）：
     - 跨 App import：只允许 Model（只读）与 api.py（复杂写操作）
     - 禁止跨 App import service/runner/consumer/state_machine
     - 所有 INSERT/UPDATE/DELETE 收敛到各 App 的 api.py
     - 前端不直连数据库；仪表盘不做写操作
     如设计引入了新跨模块依赖，列出并说明为何无法走 api.py。 -->

## Risks / Trade-offs

<!-- 已知风险与取舍：[风险] → 缓解措施 -->
