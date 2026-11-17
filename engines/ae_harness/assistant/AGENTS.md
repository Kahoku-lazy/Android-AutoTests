# engines/ae_harness/assistant AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../../AGENTS.md) → [`engines/ae_harness/AGENTS.md`](../AGENTS.md) → **本文件**。

## 1. 定位：只服务控制台调试

本目录是**给人盯着终端看的入口**，不是库。每个文件都是一个可 `python -m` 运行的调试脚本：

| 文件 | 入口 | 干什么 |
| --- | --- | --- |
| `_bootstrap.py` | —— | 控制台运行时骨架。单智能体调试入口已删除，不再作为使用入口。 |

**平台（后端任务 / 前端卡片）使用的智能体角色不在这里**，一律走 [`engines/backend_bridge/`](../../backend_bridge/AGENTS.md)。

## 2. 红线（AI 禁止事项）

1. **禁止被平台调用** —— `backend/apps` 与 `backend_bridge` 不得 `import` 本目录任何模块，也不得 `subprocess` 调这些脚本。
2. **禁止接收平台参数** —— 不接收 DB 里的 agent id、报告目录、token 上送、后端异常类型；那些属于平台入口。
3. **禁止在这里实现平台报告路径或数据库写入** —— 报告目录 `logs/agents/backend_bridge/` 与用量上送是 `backend_bridge` 的事。
4. **禁止把角色参数变成"可配置"** —— `PROVIDER` / `API_KEY_ENV` / `MODEL_NAME` / `BASE_URL` / `ROLE_KEY` / `PROMPT_NAME` 保持模块常量；要换模型就改常量或新建调试脚本，不要做成运行时选项（那是平台入口的形态）。
5. **禁止自建模型或读提示词文件** —— 一律经 `create_agent`（见 [`../agents/AGENTS.md`](../agents/AGENTS.md)）。
6. **禁止自己拼 HTML** —— 报告一律走 `event/`（[`../event/AGENTS.md`](../event/AGENTS.md)）的 `AgentEventRecorder` + `HtmlReportRenderer`。

## 3. 判断口诀

**要不要给人盯着终端看？要 → 放这里；不要，结果交给程序 → `engines/backend_bridge/`。**

## 4. 相关路径

| 用途 | 路径 |
| --- | --- |
| 上层规则（控制台 / 平台分工） | [`../AGENTS.md`](../AGENTS.md) |
| 平台侧入口 | [`../../backend_bridge/AGENTS.md`](../../backend_bridge/AGENTS.md) |
| 角色创建与红线 | [`../agents/AGENTS.md`](../agents/AGENTS.md) |
| 事件记录与报告渲染 | [`../event/AGENTS.md`](../event/AGENTS.md) |
