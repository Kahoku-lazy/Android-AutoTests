## Why

平台目前没有「平台侧自己创建并运行」的智能体角色：`engines/ae_harness/assistant/` 是控制台脚本（读 argv、打印、交互），后端无法把它当库调用；`engines/agents/` 是另一条正式链路，与 UI 执行这套 Harness 无关。结果是「平台要跑一次 UI 执行任务」没有落点。

## What Changes

- 在 `engines/backend_bridge/` 落地**平台侧 UI 执行角色**：用 `ae_harness` 的原语（`create_agent`、设备工具、事件记录器、报告渲染器、观测中间件）组装，收参数、返回结构化结果，不打印、不交互。
- 新增 `agents/`（角色装配）、`reports/`（报告路径唯一来源）、`run.py`（一次运行入口）。
- 报告输出到 `仓库根/logs/agents/backend_bridge/`（该目录已被 `.gitignore` 忽略，报告不入库）。
- 运行结果返回：报告路径、日志路径、最终文本、token 四类合计与按密钥分组、逐次用量。

**明确不做（本批）**：不写数据库、不碰 Django、不加 HTTP 接口、不改前端、不新建 token 表。

## 关联文档

- 需求来源：需求方「在 `engines/backend_bridge` 中创建一个 UI 执行智能体，使用 `ae_harness` 的方法创建」。
- 边界规则：[`engines/backend_bridge/AGENTS.md`](../../../engines/backend_bridge/AGENTS.md)（平台角色唯一落点）、[`engines/ae_harness/AGENTS.md`](../../../engines/ae_harness/AGENTS.md)（`assistant/` 只服务控制台）。
- 受影响主 spec：新建 `backend-bridge-agent`。
- 后续变更：token 入账复用 `usage_ledger.ai_usage_records`、后端接口、前端历史页（另开变更）。

## Capabilities

### New Capabilities

- `backend-bridge-agent`: 平台侧 UI 执行角色的装配、一次运行的入口契约、报告落盘位置与结果形状。

### Modified Capabilities

无。

## Impact

- 代码：新增 `engines/backend_bridge/{__init__,agents/,reports/,run}.py`；`token_usage/` 补包标记。
- 依赖方向：`backend_bridge → ae_harness`（单向），`ae_harness` 不认识 `backend_bridge`。
- 兼容性：`ae_harness` 一行不改；控制台入口零影响。
- 产物：`logs/agents/backend_bridge/<时间戳>/<时间戳>_ui_executor.{jsonl,html}`。
- 测试：新增 `tests/engines/backend_bridge/unit/`。
