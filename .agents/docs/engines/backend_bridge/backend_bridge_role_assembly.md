# backend_bridge · 平台侧智能体角色装配
> 归属模块：`engines/backend_bridge` ｜ 类型：引擎模块开发说明
> 代码真相源：`engines/backend_bridge/run.py`、`engines/backend_bridge/agents/`、`engines/backend_bridge/workflow/`、`engines/backend_bridge/reports/paths.py`
> 上级约束：engines/AGENTS.md ｜ 模块索引：engines/AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../../../../engines/AGENTS.md) → **本文件**。本目录仍在 `engines/` 内，上层红线全部适用。
> 目录现状：已是 Python 包；已有 `agents/`（角色）、`workflow/`（SOP 装配）、`events/`（事件落库）、`model_billing/`（模型费用）、`reports/`（报告路径）、`session.py`（会话）、`run.py`（入口）、`event_log.py`（事件面板）。

## 1. 定位：平台侧智能体角色的唯一落点

**平台（后端任务、前端卡片）使用的智能体角色，一律在本目录创建与运行。** `ae_harness` 只提供原语，不保存角色、提示词或流程；它的控制台入口已删除。

| 谁 | 入口在哪 | 形态 | 报告落在 |
| --- | --- | --- | --- |
| **平台**（后端 / 前端卡片） | **本目录** | 库函数：收参数、返回结构化结果 | `logs/agents/backend_bridge/` |

本目录用的原语：`ae_harness.agents.create_agent`、`ae_harness.tools`、`ae_harness.event`（记录器与渲染器）、`ae_harness.middleware`、`ae_harness.workflow.sop`。角色怎么配、提示词写什么、挂哪些工具，都由调用方传入，不回 `ae_harness` 取。

## 2. 目标结构（按需逐个落地，不预先铺空文件）

```text
backend_bridge/
  agents/            平台角色定义：调 create_agent 装配角色，挂工具与观测
  workflow/          平台编排装配：用调用方给的步骤调 ae_harness 的 SOP 抽象
  events/            事件落库：接收方绑定、运行上下文、预算计数、步骤中断、批量折叠
  reports/           报告落盘：logs/agents/backend_bridge/<时间戳>_<role>.html
  run.py             平台入口：跑一次 → 返回报告路径、token 汇总、逐次用量
  token_usage/       用量形状与上送前置（当前为空目录）
  model_billing/     模型费用计算：DeepSeek 价目、高峰倍率、8 位小数
```

## 2.1 SOP 与单角色的分工

| 维度 | 单角色（`agents/`） | SOP（`workflow/`） |
| --- | --- | --- |
| 谁做 | 一个执行者 | 执行者动手 + 验收者核对 |
| 完成判据 | 模型自己说做完 | 验收者逐条判「必须达成的结果」 |
| 步骤来源 | 无步骤 | 调用方提供的步骤 YAML（**不在引擎里保存流程**） |
| 会话语义 | 一次连接复用同一角色，多轮连续 | **不进对话页**：一次运行跑一条流程，跑完即弃 |

**SOP 只允许「使用」，不允许「自创」**：`engines/ae_harness/workflow/sop/` 是**通用抽象**（步骤模型、加载、编排执行），不保存具体流程。步骤由本目录的调用方提供。

平台侧的装配放在**本目录的 `workflow/`**：调用 `load_spec` / `run_sop`，只做三件事——装配两个角色、指定报告目录、把结果整理成返回值。**禁止**在本目录再写一套编排循环、另立步骤格式或新造验收逻辑。

**SOP 不进 AI 助手对话页**：对话页的设计只有单角色。助手测试对话由 `agents/card_agent.py` 装配、`agents/thread_run.py` 按栏复用；SOP 由平台侧入口触发，不读对话栏 snapshot。

助手名片的运营提示词由调用方传入，原样作为系统提示词。工具按「预设 + 例外」经 `agents/tool_selection.py` 过滤，仍走 `build_adb_tools()` / 只读子集。取消按 `thread_id` 登记，不写入任务号字典。

## 3. 红线（AI 禁止事项）

1. **禁止复用控制台入口** —— 不得 `import engines.ae_harness.assistant.*`，也不得用 `subprocess` 调它的脚本。
2. **禁止绕过 `create_agent` 造角色** —— 不得在本目录直接 `Agent(...)`，角色装配只经 `ae_harness.agents.create_agent`。
3. **禁止打印与交互** —— 本目录是库，不得 `print`、不得读 `sys.argv`、不得 `input()`；要给人看的信息通过返回值交给调用方。
4. **禁止自定报告路径** —— 报告一律落 `logs/agents/backend_bridge/`；路径常量只在一处定义，禁止各处拼接。
5. **禁止依赖已删除的控制台入口** —— 不得引用 `ae_harness/assistant` 或 `sop_runner`；运行参数由调用方传入。
6. **禁止在未定事项上自行决策** —— 见第 5 节，动手前先问。
7. **禁止自创 SOP** —— 步骤格式、重试、验收判定一律用 `ae_harness.workflow.sop` 的现成实现；本目录不得出现第二套编排循环或第二份步骤 YAML 格式。
8. **禁止给验收角色挂写操作工具** —— 验收侧只取勾选与只读目录的交集。
9. **事件落库只在本目录** —— 接收方绑定、运行上下文、预算计数、步骤中断与批量折叠归 `events/`；`ae_harness` 只写本地记录与报告，**禁止**在 `ae_harness` 写库或依赖后端事件类型。
10. **运行取消归本目录** —— 取消置位、当前步骤中断与清理只在本目录实现，禁止在 `ae_harness` 或后端另立第二套取消。
11. **禁止直接引用 AgentScope** —— 本目录不得 `import agentscope`；框架的消息与工具类型经 `ae_harness` 的函数取得。

## 4. 与后端的分工

- 本目录**负责**：建角色、跑一次、产 HTML 报告、把 token 用量整理成结构化数据返回、**任务事件落库前的绑定与折叠**、**运行取消**。
- 后端**负责**：从 DB 取角色配置、调用本目录入口、把用量与事件写库、对外提供报告读取接口、前端契约。
- 本目录**不负责**：DB 读写、Django 依赖、鉴权、HTTP 路由、前端。

## 5. 已定事项（曾列为未定，现已拍板）

| # | 未定 | 影响 |
| --- | --- | --- |
| 1 | 入账复用 `usage_ledger` 的 `ai_usage_records`，不新建表 | 本目录只产结构化用量，由后端写账 |
| 2 | 本目录只产数据，后端写库 | 守住 `engines/` 零 `django.*` 红线 |
| 3 | 平台角色的系统提示词由调用方传入正文 | 不在引擎里再放一份本地提示词 |
| 4 | 报告读取走「列表 + 单文件 + 路径白名单」 | `reports/` 不需要索引文件 |

以上 1–4 已落地；后续若出现新的未定项，仍按「先问再写」处理。
