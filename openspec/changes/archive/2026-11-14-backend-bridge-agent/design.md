## Context

`engines/backend_bridge/` 目前只有空的 `token_usage/` 与 `AGENTS.md`。`engines/ae_harness/` 已提供全部原语：`agents.create_agent`（返回 `AgentBundle(agent, api_key_env)`）、`tools.build_adb_tools`、`event.AgentEventRecorder` / `HtmlReportRenderer` / `summarize`、`middleware.ObservationMiddleware`。

控制台入口 `ae_harness/assistant/agent_executor.py` 做的是同一件事，但形态是 CLI（模块常量、`sys.argv`、`print_summary`、`sys.exit`）。本变更要的是同一件事的库形态。

## Goals / Non-Goals

**Goals:**

- 平台侧有一个可被后端直接调用、返回结构化结果的 UI 执行入口。
- 报告与日志落在平台自己的目录，不污染 ae_harness 的 `logs/`。
- 纯 `engines/` 内实现：不引 Django、不写库。

**Non-Goals:**

- 不做 token 入账、不建表、不做 HTTP 接口、不改前端（后续变更）。
- 不做多步 SOP、不做验收角色（本期只有执行者）。
- 不复制提示词：复用 `ae_harness` 的 `UI_EXECUTOR_PROMPT`。

## Decisions

### D1. 三个文件，各做一件事

| 文件 | 只做一件事 |
| --- | --- |
| `agents/ui_executor.py` | 装配平台 UI 执行角色：`create_agent` + 挂全量设备工具 → 返回 bundle 与观测中间件 |
| `reports/paths.py` | 报告根目录的唯一来源 + 本次运行的子目录创建 |
| `run.py` | 一次运行的入口：串起装配、跑、记录、出报告、返回结果 |

不合并成一个大文件，是为了让「角色定义」与「运行编排」各自可测。

### D2. 复用 `ae_harness` 的提示词，不复制

平台先与调试共用 `UI_EXECUTOR_PROMPT`。理由：现在复制一份 6KB 提示词，两处改一处忘一处，比共用更危险。等平台确实需要不同提示词时，再加一个 `prompts/` 目录并显式指定。

### D3. 报告路径常量只在一处

`reports/paths.py` 定义 `REPORT_ROOT = <repo>/logs/agents/backend_bridge`，并暴露 `ensure_run_dir(role) -> Path`（创建并返回本次子目录，命名为 `<时间戳>_<role>` 之类的稳定形式）。其它模块只接收 Path，不拼字符串。

`<repo>` 用 `Path(__file__).resolve().parents[3]`：`engines/backend_bridge/reports/paths.py` 往上三级是仓库根。

### D4. 结果形状用不可变数据类

返回 `UiRunResult`（frozen dataclass）：`final_text`、`report_path`、`log_path`、`tokens`（四类合计字典）、`by_api_key_env`、`usages`（逐次明细字典列表）。调用方不需要认识 `RunRecord`，也不需要解析文件。

### D5. 观测中间件由本层创建并传入

平台运行时总是挂 `ObservationMiddleware`，把它的 `records` 交给记录器。理由：平台场景更需要在事后回答「上下文压没压缩、提示词是什么」，而控制台可以按需手动加。

### D6. 不做异常包装

本层不新增自定义异常类型（`engines/` 红线）。底层抛什么就透传什么：`create_agent` 的 `ValueError`、AgentScope 的异常、IO 错误。由调用方（后端）决定如何映射成业务错误。

## 模块防火墙自检

| 红线 | 是否触碰 | 说明 |
| --- | --- | --- |
| 跨 App import / 写库 / 前端 | 否 | 本层不引 Django、不写库 |
| `engines/` 零 `django.*` / `apps.*` | 是（新增约束） | 由测试守护：本目录导入只允许 `ae_harness` 与标准库 |
| 角色只经 `create_agent` 装配 | 是（遵守） | 不直接 `Agent(...)` |
| 不复用控制台入口 | 是（遵守） | 不 import `ae_harness.assistant` |
| 新增自定义异常 | 否 | 不新增 |

## Risks / Trade-offs

- **与 `assistant/agent_executor.py` 有约 20 行装配重复** → 有意接受：平台不依赖控制台脚本。若重复继续增长，再抽公共函数。
- **报告目录被 gitignore** → 报告是运行产物，不入库是预期；但**前端读取需要后端接口**，属下一批。
- **`parents[3]` 依赖目录深度** → 换位置会错；用单测断言 `REPORT_ROOT` 的末三级是 `logs/agents/backend_bridge`。
- **固定挂观测中间件会增大产物** → 全量模式默认开，平台报告本就为重放设计；如过大可显式关观察。

## Migration Plan

1. 先落三个文件 + 包标记，不动任何既有代码。
2. 单测覆盖路径、结果形状、导入边界；真机跑一次验证报告产出。
3. 回滚：删除本目录新增文件即可，`ae_harness` 与后端均未改动。

## Open Questions

- 平台是否需要独立的验收角色（执行 + 验收成对）：本期不做，等有明确的「验收判据落库」需求再开。

### D7. 报告读取复用路径常量 + 白名单，不开放任意路径

`ai_assistant` 直接 import `engines.backend_bridge.reports.REPORT_ROOT`（依赖方向 backend → engines 允许），列表与读取都在 `ai_assistant/reports.py` 里做白名单校验：目录名必须是 `<8位日期>_<6位时间>_<角色>`，文件名必须是 `<名字>.<html|jsonl>`，解析后再断言仍在根内。

不采用「把 logs/ 挂成静态目录」：静态目录要么放开整个 logs/（越权），要么引入额外的静态根配置，且无法按运行目录过滤。

### D8. 用量复用既有账本，幂等键按「来源:执行ID:轮次」

不新建 token 表：`ai_usage_records` 已有唯一 `event_id`、四类 token 与费用列。幂等键 `agent:<execution_id>:<round>` 保证重跑同一次执行不会翻倍。

厂商由密钥环境变量名推断（`GOVEE_*` → `govee` → 账本归一为 `deepseek`），与账本「只有两类厂商」的约束一致；金额交给账本按价目表算，本层不伪造费用。

### D9. 先给一次性命令，不抢跑任务体系

平台目前没有 HTTP 触发口，而接入 `task_list` 的任务体系需要新任务类型与 runner 分支（会改动任务状态机、花费归集、前端任务列表）。本批先提供 `python manage.py run_ui_agent "<任务>"`，把「跑 → 出报告 → 入账」打通并可验证；HTTP 触发与任务体系接入留作下一变更，调用的是同一对函数。
