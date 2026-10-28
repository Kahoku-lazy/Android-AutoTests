## Why

设备控制任务跑一条用例要几分钟到几十分钟，期间要点几百次模型。现在任何一次 `429` / 5xx / 连接超时都会把整条用例打成失败，用户看到的是「任务失败」，而不是「重试后照常跑完」——一次瞬时限流要重跑整条 SOP，代价极高。

排查框架代码后发现**已有两层机制，但都不够用**：

- 模型层（`ChatModelBase.__call__` → `agentscope/model/_base.py:206`）已经重试：`max_retries=3`、**固定 `retry_delay=1.0s`**、只重试 provider 自己声明的异常类型，且**只包住 `_call_api` 的请求建立阶段**；
- 智能体层（`agentscope/agent/_agent.py:3301`）支持 `model_config.fallback_model`，但我们建 `Agent` 时**没有传 `model_config`**（`engines/agents/role/base.py:49`），所以 `max_retries=0`、也没有备用模型。

于是真空中三件事没人管：① 限流恢复常需 ≫3 秒，固定 1s 的三次重试顶不住；② 主模型彻底不可用时没有备用模型接管；③ 流式响应**已经产出内容后**断开时框架不重试，我们的角色又是 `stream=True`，这类失败直接冒到任务层。

## What Changes

- 新增 `engines/agents/middleware/model_retry.py`：
  - `ModelRetryMiddleware`（`MiddlewareBase` 的 `on_model_call`）：**指数退避重试** + **备用模型回退** + **统一警告日志**（写 `agent_event_log`，带模型名 / 第几次尝试 / 原因）；
  - 瞬态判定 `is_transient_model_error()`：HTTP 408/409/425/429/5xx、超时 / 连接类异常名、以及常见限流文案；`400/401/403/404`、参数校验、代码缺陷类异常**不重试**；
  - 流式保护：**首块之前**失败才重试，已产出内容后失败直接抛出，避免两段内容拼接；
  - 环境变量配置：`AGENT_MODEL_RETRY_ATTEMPTS`（默认 2 = 总共两次调用）/ `AGENT_MODEL_RETRY_BASE_DELAY_MS`（默认 800）/ `AGENT_MODEL_RETRY_MAX_DELAY_MS`（默认 8000）/ `AGENT_FALLBACK_MODEL`（默认空 = 不启用回退）/ `AGENT_FALLBACK_PROVIDER` / `AGENT_FALLBACK_BASE_URL` / `AGENT_FALLBACK_API_KEY`。
- `engines/agents/role/base.py`：`BaseRole.__init__` 给 `Agent(middlewares=...)` 装配上述中间件；备用模型用既有 `ChatModelFactory` 按角色同一套 `stream` / `vision` 构造，未配置或未启用时返回空列表（零开销）。
- 新增单元测试 `tests/graybox/unit/test_model_retry_middleware.py`：分类判定、退避序列、重试用尽、回退成功/回退亦失败、流式首块前/后、环境变量解析、未启用不装配。

不改：提交契约、任务状态机、事件类型、计费口径；`ChatModelFactory` 与其它模块的模型构造保持原样。

## 关联文档

- `openspec/specs/agent-role-run/spec.md`：角色运行入口语义不变，本变更只在其内部增加韧性层。
- `openspec/specs/sop-task-run/spec.md`：任务预算与失败口径不变；重试耗时不改变「一次任务只有一份 YAML」等既有要求。
- 框架依据：`agentscope 2.0.9` 的 `model/_base.py:206`（模型层重试）、`agent/_agent.py:3301`（agent 层 fallback）、`middleware/_base.py:213`（`on_model_call` 契约）。

## Capabilities

### New Capabilities

- `agent-model-resilience`：模型调用的退避重试、备用模型回退与流式不重放。

### Modified Capabilities

（无）

## Impact

- 新增：`engines/agents/middleware/__init__.py`、`engines/agents/middleware/model_retry.py`、`tests/graybox/unit/test_model_retry_middleware.py`
- 修改：`engines/agents/role/base.py`（装配三行 + 一个构造备用模型的小方法）
- 运行时：默认开启同模型 1 次额外重试（最坏耗时增加约 1s 量级）；回退需显式配置 `AGENT_FALLBACK_MODEL` 才生效
- 不影响：Django 侧任何接口与落库；`agent_event_log` 只多出重试警告行
