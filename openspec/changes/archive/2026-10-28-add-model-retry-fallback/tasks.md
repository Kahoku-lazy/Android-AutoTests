## 1. 判据与设计

- [x] 1.1 复核框架已有机制，确认「真空」在哪：模型层 `ChatModelBase.__call__`（`agentscope/model/_base.py:206`）已有 `max_retries=3` + 固定 `retry_delay=1.0s`，只重试 provider 声明的异常且只包 `_call_api` 请求建立阶段；agent 层支持 `model_config.fallback_model`（`agent/_agent.py:3301`），但 `BaseRole` 建 `Agent` 时没传 `model_config` → 判定三个真空：退避太短、无备用模型、流式响应在首块之后断开不重试
- [x] 1.2 取舍写入 `design.md`：D1 只补一层不重写模型层重试；D2 回退只在瞬态故障后；D3 流式只重试首块之前；D4 中间件无状态；D5 配置走环境变量不碰数据库；D6 日志写 `agent_event_log`
- [x] 1.3 规格增量落在新能力 `agent-model-resilience`（三条要求：退避重试 / 备用模型回退 / 已输出流式内容不重放），`openspec validate --strict` 通过

## 2. 实现

- [x] 2.1 新增 `engines/agents/middleware/model_retry.py`：`is_transient_model_error`（408/409/425/429/5xx、超时/连接类异常名、限流文案；400/401/403/404 与参数校验类不重试）、`RetrySettings` / `load_retry_settings`（4+3 个环境变量、非法值回落默认）、`ModelRetryMiddleware.on_model_call`（指数退避 + 备用模型 + 警告日志 + 流式首块探针）、`build_model_retry_middleware`
- [x] 2.2 新增 `engines/agents/middleware/__init__.py` 导出上述符号（此前该目录为空）
- [x] 2.3 `engines/agents/role/base.py`：`Agent(..., middlewares=self._middlewares())`；新增 `_middlewares()` 与 `_fallback_model()`（备用模型复用 `ChatModelFactory`，沿用角色的 `stream` / `vision`）；未启用时返回空列表
- [x] 2.4 `.env.example` 增「模型调用重试与回退」段，列出 7 个环境变量与默认值

## 3. 验证

- [x] 3.1 `python -m pytest -c tests/pytest.ini tests/graybox/unit/test_model_retry_middleware.py -q` → **31 passed**（分类判定 13 例、退避序列、重试用尽、回退成功/回退亦失败、非瞬态不重试也不回退、流式首块前/后、空流、参数校验、环境变量默认值与解析、启用/未启用装配、`BaseRole` 装配两条）
- [x] 3.2 真 Agent 端到端探针（`temps/probe_middleware_reply.py`）：在主模型 `_call_api` 注入一次 503 → **模型调用 2 次、最终文本 `done`**，`logs/agents/agent_events.log` 出现 1 条 WARNING「第 1/2 次：deepseek-flash · _Err503」
- [x] 3.3 装配探针（`temps/probe_middleware_wiring.py`）：`middlewares=['ModelRetryMiddleware']`、`fallback=deepseek-pro`、`attempts=2`
- [x] 3.4 `ruff format --check` / `ruff check`（engines/agents/middleware、role/base.py、新测试文件）→ 全部通过
- [x] 3.5 `python run.py check` → **与本次变更相关的检查全绿**（django-check / ruff-format / ruff-lint / pytest-collect / ruff-engines-format / ruff-engines-lint / boundary / vue-tsc / vitest / vite-build 均 PASS）；整体 18/22 的 4 项失败全部指向另一条在途改动：`openapi-schema` 与 `openapi-coverage` 因未跟踪的新应用 `backend/apps/knowledge_assistant` 的 `/api/knowledge-assistant/status/` 未进 `openspec/openapi.yaml`，`prettier` 与 `prettier-ts` 因 `frontend/src/modules/knowledge-assistant/**` 6+4 个文件未格式化 —— 与本变更无交集。
- [x] 3.6 `python -m pytest -c tests/pytest.ini tests/graybox/unit -q`（既有单元套件回归）→ 有改动 **45 failed / 416 passed**，把 `role/base.py` 还原到 HEAD 后 **46 failed / 418 passed**；两次失败集合逐条比对只差一条 —— 我新增的 `test_base_role_wires_middleware_when_enabled`（还原后必然失败）。结论：**没有既有用例被本次改动打挂**；那 45 条失败全部来自另一条在途改动（`ai-assistant/ToolDebugPage.vue`、`helpers/tool-debug-label.ts`、`api/toolbox.ts` 已删除、`workflow/__init__.py` 不再导出 `SopStepInput`，knowledge-assistant 新模块未注册 OpenAPI），与本变更无交集。

- [x] 3.6 残留检查：`tests/` 与 `engines/` 内无对 `AGENT_FALLBACK_MODEL` 的硬编码密钥；日志行不含 api_key（`RetrySettings.fallback_api_key` 用 `repr=False`）
