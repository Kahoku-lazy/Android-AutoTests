# engines/ae_harness AGENTS.md

本目录是 `engines/` 下的**独立原型链路**：只做「手机 UI 执行 + 验收」这一条链，不接后端、不写事件库、不参与平台任务。

> 与 [`engines/agents/`](../agents/AGENTS.md) 的关系：两者是同一能力的两种实现，`agents/` 是接平台的正式版，本目录不替代它。当前**无任何代码 import 本包**，也没有对应测试；是否合并/替换须先走 OpenSpec 变更。

## 与控制台 / 平台的分工（红线）

**`assistant/` 只服务控制台调试；平台使用的智能体角色一律走 [`engines/backend_bridge/`](../backend_bridge/AGENTS.md)。**

| 谁 | 入口在哪 | 形态 | 产物落在 |
| --- | --- | --- | --- |
| **控制台**（开发者调试） | 本包 `assistant/*`，以及 `workflow/sop_runner.py` | CLI 脚本：读 `sys.argv`、打印汇总、交互循环 | 本包 `logs/` |
| **平台**（后端任务 / 前端卡片） | `engines/backend_bridge/`（角色与编排装配都在那里） | 库函数：收参数、返回结构化结果 | `logs/agents/backend_bridge/` |

**`workflow/sop/` 不属于控制台**：它是通用的 SOP 抽象（步骤模型、加载、编排执行、步骤 YAML），控制台与平台都从它调用。控制台侧的装配是 `workflow/sop_runner.py`；平台侧的装配在 `engines/backend_bridge/workflow/`。**两边都只调抽象，不复制实现。**

本包只提供**原语**：`agents.create_agent`、`tools`、`event`（记录器与渲染器）、`middleware`（观测）。两份入口共享原语，各自装配。

**禁止**：

1. **禁止**让 `backend/apps` 或 `backend_bridge` 直接调用 `assistant/` 下的脚本入口（那是 CLI，不是库）。
2. **禁止**把平台专用参数塞进 `assistant/` 的入口：DB 里的 agent id、报告目录、token 上报、后端异常类型。
3. **禁止**在 `assistant/` 里实现平台报告路径或数据库写入；平台侧报告目录与用量上送归 `backend_bridge`。

判断口诀：**要不要给人盯着终端看？要 → `assistant/`；不要，结果是交给程序的 → `backend_bridge/`。**

## 目录结构

```text
ae_harness/
  agents/              角色定义：config → models → creator
    config/prompts/    各角色的系统提示词
  assistant/           角色调试入口：建角色、挂工具、跑一轮、出报告
    _bootstrap.py      入口运行时引导：编码 / 日志级别 / 汇总 / 异常包装
  tools/adb/           adb 工具（16 个）+ 只读子集
  event/               事件记录与报告渲染（含用量记录、全量模式）
  middleware/          三类中间件：只读观测、模型调用重试、运行控制（预算/取消）
  workflow/            多智能体编排：sop/ 是 SOP 实现，steps/*.yaml 是步骤定义
  logs/<时间戳>/        每轮一份 jsonl + html
```

## 各目录职责

| 位置 | 负责 | 不负责 |
| --- | --- | --- |
| `agents/` | 模型配置、提示词、Agent 创建 | 跑任务、挂工具、出报告 |
| `assistant/` | 某个角色的可运行入口；`_bootstrap.py` 提供运行时骨架 | 定义角色、造模型、渲染报告 |
| `tools/adb/` | 设备动作与返回值 | 决策、编排、读配置 |
| `event/` | 记录事件、渲染报告、用量记录与汇总 | 改 Agent、写业务逻辑 |
| `middleware/` | 三类横切：只读观测、失败重试、预算/取消 | 扩展能力、换动作、落盘 |
| `workflow/` | 多智能体编排（SOP）：步骤 YAML、执行者 + 验收者循环 | 建角色、造模型、渲染 HTML |

## 红线（AI 禁止事项）

### 一、放置

1. **禁止在仓库根放脚本** —— 角色入口一律放 `assistant/`，工具一律放 `tools/<域>/`。
2. **禁止在 `ae_harness/` 根新增模块** —— 根目录只留 `__init__.py` 与 `AGENTS.md`；新能力进对应子目录。
3. **禁止把工具文件堆在 `tools/` 根上** —— 必须进 `tools/<域>/`。
4. **禁止在 `workflow/sop/` 以外的位置重写编排** —— 步骤推进、重试、驳回记录都由 `run_sop` 负责；新流程先扩展步骤 YAML，不要另写一套循环。

### 二、职责

5. **禁止绕过 `create_agent` 造 Agent** —— 不得在别处直接 `Agent(...)`，不得新增第二种创建入口。
6. **禁止在 `agents/` 以外读配置** —— `.env`、`models.yaml`、提示词只能经 `agents/config.py`。
7. **禁止在 `assistant/` 造模型或读提示词** —— 入口只调 `create_agent`，不自建客户端、不 `open()` 提示词文件。
8. **禁止 `event/` 引用具体工具名** —— 工具特有展示由调用方通过 `step_extras` 注册。
9. **禁止 `tools/` 反向依赖 `agents/`** —— 工具不知道 Agent 存在，两者只在入口汇合。
10. **禁止在 `tools/` 里做决策或编排** —— 每个工具只做一个动作，多步流程由 Agent 决定。

### 二之二、异常类登记（按 engines 红线先立项）

新增自定义异常必须先在子 AGENTS 立项。当前只有两个，且只在运行控制里用：

| 异常 | 位置 | 语义 | 调用方该记成 |
| --- | --- | --- | --- |
| `BudgetExceeded` | `middleware/control.py` | 模型调用次数或时长超限 | **中止**，不是失败 |
| `RunCancelled` | `middleware/control.py` | 外部置位取消 | **取消**，与失败分开 |

**禁止**再新增同类异常（例如 `TimeoutStop`、`UserAborted`），要区分新语义先改本表。

### 三、能力边界

11. **禁止引入串口、视觉、语音、TTS、向量、知识库** —— 本目录只做「手机 UI 执行 + 验收」这一条链路。
12. **禁止给验收角色挂写操作工具** —— 验收侧固定用 `build_adb_readonly_tools()`，从工具层杜绝改设备状态。

## 新增一个角色的标准路径

1. 提示词写到 `agents/config/prompts/<NAME>_PROMPT.md`。
2. 在 `assistant/` 建 `agent_<role>.py`，照抄现有两个入口的骨架（`build_agent` / 主循环 / `_run`）。
3. 角色定义只调 `create_agent`；工具用 `build_adb_tools()` 或 `build_adb_readonly_tools()` 逐个 `add_tool`。
4. 运行骨架统一用 `assistant/_bootstrap.py`：`configure_runtime()` + `print_summary()` + `run_main()`。
5. 报告统一用 `event/`：`AgentEventRecorder` + `HtmlReportRenderer`，不要自己拼 HTML。

## 当前可运行入口

```bash
# 单角色调试
python -m engines.ae_harness.assistant.agent_executor "打开设置，进入关于手机"
python -m engines.ae_harness.assistant.agent_verifier "屏幕上能看到「关于手机」标题"

# 多智能体编排（SOP）
python -m engines.ae_harness.workflow.sop_runner
python -m engines.ae_harness.workflow.sop_runner --spec 其他.yaml "自定义任务"
```
