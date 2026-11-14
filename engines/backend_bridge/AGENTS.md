# engines/backend_bridge AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../AGENTS.md) → **本文件**。本目录仍在 `engines/` 内，上层红线全部适用。
> 目录现状：**尚未成为 Python 包**（无 `__init__.py`），目前只有一个空的 `token_usage/`。

## 1. 定位：平台侧智能体角色的唯一落点

**平台（后端任务、前端卡片）使用的智能体角色，一律在本目录创建与运行；控制台调试入口在 [`engines/ae_harness/assistant/`](../ae_harness/AGENTS.md)。**

| 谁 | 入口在哪 | 形态 | 报告落在 |
| --- | --- | --- | --- |
| **控制台**（开发者调试） | `engines/ae_harness/assistant/*` | CLI 脚本：读 `sys.argv`、打印、交互循环 | `engines/ae_harness/logs/` |
| **平台**（后端 / 前端卡片） | **本目录** | 库函数：收参数、返回结构化结果 | `logs/agents/backend_bridge/` |

两者**只共享原语**：`ae_harness.agents.create_agent`、`ae_harness.tools`、`ae_harness.event`（记录器与渲染器）、`ae_harness.middleware`（观测）。各自装配，互不调用对方的入口。

判断口诀：**要不要给人盯着终端看？要 → `ae_harness/assistant/`；不要，结果交给程序 → 本目录。**

## 2. 目标结构（按需逐个落地，不预先铺空文件）

```text
backend_bridge/
  agents/            平台角色定义：调 create_agent 装配角色，挂工具与观测
  reports/           报告落盘：logs/agents/backend_bridge/<时间戳>_<role>.html
  run.py             平台入口：跑一次 → 返回报告路径、token 汇总、逐次用量
  token_usage/       用量形状与上送前置（当前为空目录）
```

## 3. 红线（AI 禁止事项）

1. **禁止复用控制台入口** —— 不得 `import engines.ae_harness.assistant.*`，也不得用 `subprocess` 调它的脚本。
2. **禁止绕过 `create_agent` 造角色** —— 不得在本目录直接 `Agent(...)`，角色装配只经 `ae_harness.agents.create_agent`。
3. **禁止打印与交互** —— 本目录是库，不得 `print`、不得读 `sys.argv`、不得 `input()`；要给人看的信息通过返回值交给调用方。
4. **禁止自定报告路径** —— 报告一律落 `logs/agents/backend_bridge/`；路径常量只在一处定义，禁止各处拼接。
5. **禁止把控制台参数塞进来** —— `_bootstrap` 的运行时引导、汇总打印、交互循环属于控制台，不属于本目录。
6. **禁止在未定事项上自行决策** —— 见第 5 节，动手前先问。

## 4. 与后端的分工（仍在演进，动手前确认）

- 本目录**负责**：建角色、跑一次、产 HTML 报告、把 token 用量整理成结构化数据返回。
- 后端**负责**：从 DB 取角色配置、调用本目录入口、把用量写库、对外提供报告读取接口、前端契约。
- 本目录**不负责**：DB 读写、Django 依赖、鉴权、HTTP 路由、前端。

## 5. 未定事项（禁止 AI 自行假设）

| # | 未定 | 影响 |
| --- | --- | --- |
| 1 | token 入账复用 `usage_ledger` 的 `ai_usage_records`，还是新建表 | 决定本目录是否要产 `token_usage` 形状 |
| 2 | 写库方式：本目录只产数据、后端注入 sink 写入，还是本目录直接 ORM | 直接 ORM 会破 `engines/` 零 `django.*` 红线，需先获批 |
| 3 | 平台角色复用 `ae_harness` 的 `UI_EXECUTOR_PROMPT`，还是本目录自维护平台提示词 | 决定提示词放在哪 |
| 4 | 报告读取接口的形态（列表 + 单文件、路径白名单） | 决定 `reports/` 是否需要索引文件 |

**在 1–4 定下来之前，不要新增业务代码**；可以先补目录骨架与文档。
