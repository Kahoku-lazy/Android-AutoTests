# engines/ae_harness/assistant AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../../AGENTS.md) → [`engines/ae_harness/AGENTS.md`](../AGENTS.md) → **本文件**。

## 1. 定位：控制台入口已删除

本目录不再放角色入口。`agent_executor.py`、`agent_verifier.py` 已删除，只剩 `_bootstrap.py` 这个运行时骨架，且没有调用方。

**平台使用的智能体一律在 [`engines/backend_bridge/`](../../backend_bridge/AGENTS.md) 装配**，不回这里新增脚本。

## 2. 红线（AI 禁止事项）

1. **禁止被平台调用** —— `backend/apps` 与 `backend_bridge` 不得 `import` 本目录任何模块，也不得 `subprocess` 调这些脚本。
2. **禁止接收平台参数** —— 不接收 DB 里的 agent id、报告目录、token 上送、后端异常类型；那些属于平台入口。
3. **禁止在这里实现平台报告路径或数据库写入** —— 报告目录 `logs/agents/backend_bridge/` 与用量上送是 `backend_bridge` 的事。
4. **禁止在这里新增可运行脚本** —— 要跑一轮，在 `backend_bridge` 加库函数，参数由调用方传入。
5. **禁止自建模型或读提示词文件** —— 一律经 `create_agent`（见 [`../agents/AGENTS.md`](../agents/AGENTS.md)）。
6. **禁止自己拼 HTML** —— 报告一律走 `event/`（[`../event/AGENTS.md`](../event/AGENTS.md)）的 `AgentEventRecorder` + `HtmlReportRenderer`。

## 3. 相关路径

| 用途 | 路径 |
| --- | --- |
| 上层规则（控制台 / 平台分工） | [`../AGENTS.md`](../AGENTS.md) |
| 平台侧入口 | [`../../backend_bridge/AGENTS.md`](../../backend_bridge/AGENTS.md) |
| 角色创建与红线 | [`../agents/AGENTS.md`](../agents/AGENTS.md) |
| 事件记录与报告渲染 | [`../event/AGENTS.md`](../event/AGENTS.md) |
