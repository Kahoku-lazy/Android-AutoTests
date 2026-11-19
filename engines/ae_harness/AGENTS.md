# engines/ae_harness AGENTS.md

本目录是 `engines/` 下的**Agent 原语层**：只提供可复用的能力（造智能体、工具、事件记录与报告渲染、中间件、SOP 抽象、只读知识检索），不定义角色、不保存提示词、不决定跑哪条流程，不接后端、不写数据库。

> 与 [`engines/backend_bridge/`](../backend_bridge/AGENTS.md) 的关系：本目录只出原语，**角色、提示词、工具勾选与流程装配一律在 `backend_bridge`**。`backend_bridge` 的生产代码 import 本包的 `agents` / `tools` / `event` / `middleware` / `workflow.sop` 五个子包。

角色从哪来：调用方把提示词正文、厂商、密钥名、模型名传给 `create_agent`，再自己挂工具。平台的提示词与模型来自运营库，经 `backend_bridge` 传入。

`workflow/sop/` 是通用的 SOP 抽象（步骤模型、加载、编排执行）。它不建角色、不挂工具；步骤 YAML 由调用方准备。平台侧的装配在 `engines/backend_bridge/workflow/`，只调 `load_spec` / `run_sop`，不复制实现。

## 目录结构

```text
ae_harness/
  agents/              造智能体：models → creator；config 只读日志关键词
  assistant/           只剩 _bootstrap.py，控制台角色入口已删除
  tools/adb/           adb 工具 + 只读子集
  tools/case_library/  用例库工具，写入函数由调用方注入
  tools/document/      只读文档工具，正文由调用方注入
  tools/catalog.py     只读工具目录，不含实现
  knowledge/           独立知识库模块：向量模型配置、索引、只读检索工具（整目录可删）
  event/               事件记录与报告渲染（含用量记录、全量模式）
  middleware/          三类中间件：只读观测、模型调用重试、运行控制（预算/取消）
  workflow/sop/        SOP 抽象：步骤模型、加载、编排执行
```

## 各目录职责

| 位置 | 负责 | 不负责 |
| --- | --- | --- |
| `agents/` | 校验连接参数、造模型、按调用方传入的正文造智能体 | 定义角色、保存提示词、跑任务、挂工具 |
| `assistant/` | `_bootstrap.py` 留着运行时骨架 | 角色入口已删除，不再新增 |
| `tools/` | 按域提供动作与返回值；`catalog.py` 只列名字 | 决策、编排、读配置、知道 Agent 存在 |
| `knowledge/` | 向量模型配置、按库索引、只读检索工具 | 文档上传、知识库写接口、改 Agent、渲染报告 |
| `event/` | 记录事件、渲染报告、用量记录与汇总 | 改 Agent、写业务逻辑 |
| `middleware/` | 三类横切：只读观测、失败重试、预算/取消 | 扩展能力、换动作、落盘 |
| `workflow/sop/` | 步骤模型、加载、编排执行 | 建角色、造模型、挂工具、决定流程内容 |

## 红线（AI 禁止事项）

### 一、放置

1. **禁止在仓库根放脚本** —— 工具一律放 `tools/<域>/`；**唯一例外**是知识库自带的检索工具，随 `knowledge/` 走（见第 11 条）。
2. **禁止在 `ae_harness/` 根新增模块** —— 根目录只留 `__init__.py` 与 `AGENTS.md`；新能力进对应子目录。
3. **禁止把工具文件堆在 `tools/` 根上** —— 必须进 `tools/<域>/`。
4. **禁止在 `workflow/sop/` 以外的位置重写编排** —— 步骤推进、重试、驳回记录都由 `run_sop` 负责；新流程由调用方提供步骤数据，不要另写一套循环。

### 二、职责

5. **禁止绕过 `create_agent` 造 Agent** —— 不得在别处直接 `Agent(...)`，不得新增第二种创建入口。
6. **禁止在 `agents/` 读角色提示词文件** —— 系统提示词由调用方传入正文，本目录不维护 `prompts/`。聊天模型不再有 `models.yaml`：连接参数由调用方传给 `create_model`，密钥由 `models.py` 自己读仓库根 `.env`。**豁免**：其它子包自带的配置（例如 `knowledge/config/`）由其自读自校验；`.env` 全仓只有仓库根一份，允许子包自带取值函数，但**不得新增第二份 `.env`**。
7. **禁止在 `assistant/` 新增入口** —— 控制台角色脚本已删除；新的可运行入口放 `backend_bridge`，不回这里。
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

11. **禁止引入串口、视觉、语音、TTS** —— 本目录提供的是通用能力，不承载一条具体业务流程。**知识库只允许只读检索**：模块放根级 `knowledge/`（**不进 `tools/`**），以只读工具形态由调用方挂载；禁止在本目录做文档上传、知识库写接口或任何文档库运营面。
12. **禁止在本目录决定谁能写** —— 只读子集由 `build_*_readonly_tools()` 提供；验收者只挂只读工具是 `backend_bridge` 的装配规则，不在这里写死角色。

## 新增一个能力的标准路径

1. 系统提示词由调用方传入正文，不在本目录新增提示词文件，也不新增角色脚本。
2. 新工具进 `tools/<域>/`，并在 `tools/catalog.py` 登记域与只读子集。
3. 角色装配放 `backend_bridge`：只调 `create_agent`，再按调用方的勾选挂工具。
4. 报告统一用 `event/`：`AgentEventRecorder` + `HtmlReportRenderer`，不要自己拼 HTML。
