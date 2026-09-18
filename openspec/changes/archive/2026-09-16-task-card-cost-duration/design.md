## Context

任务列表走 `serialize_agent_task_row`，详情走 `serialize_agent_task_detail`（已含 `deepseek_cost` / `started_at` / `finished_at`）。卡片 `TaskBoard.vue` meta 仅有状态、创建、设备、助手。费用函数 `task_deepseek_cost` 已存在，详情页耗时用 `formatTaskDuration`。

## Goals / Non-Goals

**Goals:**
- 列表 DTO 复用详情的费用与时间字段，不新增计价逻辑
- 卡片增加两行 meta，格式与详情一致

**Non-Goals:**
- 不落库费用字段、不改 token 采集
- 不改详情 KPI、不改仪表盘
- 执行中不按「当前时刻」实时倒计时（无 finished_at 则耗时为 —；列表 5s 轮询只刷新已落库字段）

## Decisions

1. **费用在后端按任务计算后下发，不在前端重算**  
   理由：高峰时段与分模型单价已在 `deepseek_billing`；列表与详情必须同值。  
   备选：前端按 token 再算一遍 — 易漂移，否决。

2. **耗时由前端用 `started_at`/`finished_at` 格式化，不下发 duration 字符串**  
   理由：详情已有 `formatTaskDuration`；列表补时间戳即可。  
   备选：后端下发秒数 — 多余契约，否决。

3. **卡片只加 meta 行，不改 sticky 色/布局骨架**  
   理由：用户要求「先内容」；高度随内容增高即可。

## 模块防火墙自检

- 不跨 App import；列表序列化仍在 `ai_assistant.api`
- 无新增写库
- 前端仍只走 `/api/ai/agent-tasks`

## Risks / Trade-offs

- [列表对每行调用 `task_deepseek_cost`] → 纯内存算术，任务量与现列表同阶，可接受
- [执行中耗时显示 —] → 与详情 KPI 一致；避免前端用本机时钟漂移
