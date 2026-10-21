## Why

「AI 用量」当前把 5 张 KPI 卡横向铺满、智能体卡单独放在下方，右侧大片留白；费用只用一张卡承载累计与今日，靠副标题区分，阅读成本高。按要求重组为左侧 3+2、右侧智能体卡，并把费用拆成两张明确的卡。

## What Changes

- 「任务数量」卡从「AI 用量」移到「平台运营」，插在「运行中任务」之后、「工作流」之前，保持无独立「进入」按钮。
- 「累计 Token」改名「累计用量」，「当天 Token 用量」改名「当天用量」；两者与「缓存命中率」组成左侧第一行，按此顺序排列，三张卡都去掉副标题。
- 「DeepSeek 费用」拆成「总费用」与「当天费用」两张卡，放在左侧第二行；两张卡的副标题都固定为「DeepSeek」，仍按三位有效数字、单位元显示。
- 智能体用量卡（如 Agent-01）从 KPI 卡下方移到右侧列，与左侧两行并排；仍显示缓存命中、输入、输出、总费用四项。
- 统计接口、`ai_usage` 字段与后端聚合不变。

## 关联文档

- PRD-01 仪表盘

## Capabilities

### New Capabilities

### Modified Capabilities

- `dashboard-ai-usage`: AI 用量区块的卡片集合、标题、位置与费用拆分
- `dashboard-chapter-boards`: 平台运营章节新增「任务数量」卡及五卡顺序

## Impact

- `frontend/src/modules/dashboard/index.vue`：平台运营加卡、AI 用量重排、智能体卡移入右列
- `frontend/src/modules/dashboard/DashboardView.style.css`：新增 AI 两列布局与响应式规则
- `frontend/tests/dashboard/`：按需补充展示/格式化单测
- 后端聚合与 `GET /api/dashboard/stats/` 契约不变
