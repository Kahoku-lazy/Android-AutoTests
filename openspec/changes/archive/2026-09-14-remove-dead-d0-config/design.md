## Context

- 「零消费」判定证据：8 个符号逐个全仓 grep，命中仅落在 `config/settings.py`（定义处）与 `config/agentscope_config.py`（死模块自读）；`openspec/specs/` 零引用。
- `.env` 被 `.gitignore:70` 忽略 → 属本地环境，不在版本控制内，本变更不修改它。
- `config/settings.py` 的 `_load_dotenv()` 在导入时读 `.env`，因此删配置不影响 `manage.py check` 所需的 `DJANGO_SECRET_KEY`。

## Goals / Non-Goals

**Goals:**

- 让 D0 只剩**被消费**的装配配置；删掉「平台有独立 AgentScope 服务」的误导残留。

**Non-Goals:**

- 不改安全默认值（D0-5 `ALLOWED_HOSTS="*"` / D0-6 `CORS_ALLOW_ALL_ORIGINS=True`）。
- 不动 `config/api_docs.py`（D0-9，三份真相源问题）。
- 不修 ARCH-00 的另两处漂移（`DEVICE_ENGINE` 默认值、`DEVICE_SESSION_ENABLED` 幽灵开关）——已在 proposal 登记为范围外。
- 不删 `data/agentscope_workspaces` 目录与数据。

## Decisions

**D1 整块删 `# ── AgentScope ──`，而不是逐项删。**
5 项彼此不独立（`PORT` 被 `URL` 的默认值引用、`TITLE/VERSION/WORKSPACE_DIR` 只被死模块读）；整块删更清晰、不留半条死链。
备选：只删「零消费」的 `URL`/`WORKSPACE_DIR` 留 `PORT/TITLE/VERSION` —— 那三项的唯一消费者是本次要删的死模块，留下即为死配置。

**D2 保留 `data/agentscope_workspaces` 目录。**
删除配置 ≠ 删除数据；目录内可能有运行时产物。
备选：一并删除 —— 有数据丢失风险，不做。

**D3 保留 `DEVICE_SERIAL` 与 `SERVER_PORT`。**
两者有真实消费：`tools/dump_ui.py:66,68` 与 `run.py:50,61` + `frontend/vite.config.js:56-59`。

**D4 ARCH-00 只删 `AIRTEST_ENABLED` 行。**
同表的 `DEVICE_ENGINE` / `DEVICE_SESSION_ENABLED` 两处漂移与本次删除无关，登记不改，避免夹带范围外改动。

## 模块防火墙自检

纯删除零消费配置，无代码 import 关系变化：

- **跨 App import**：无新增，反而减少（删除的模块无人 import）。
- **禁止跨 App import service/runner/consumer/state_machine**：不涉及。
- **所有写库收敛到 api.py**：不涉及，无任何写库改动。
- **前端不直连数据库**：不涉及。
- **结论**：无新依赖，无需走 `api.py`。

## Risks / Trade-offs

- [若有代码以 `getattr(settings, "AGENTSCOPE_SERVICE_URL", ...)` 之类动态方式读取，grep 会漏] → 已按 `getattr(settings` 模式补扫；并以 `manage.py check` + 边界扫描兜底。
- [`.env` 里仍留 `AGENTSCOPE_PORT` / `SCREENSHOT_INTERVAL` 两键，接手者可能困惑] → 在 proposal 登记；不代改本地 `.env`（被 gitignore）。
- [ARCH-00 其他章节仍提 `DEVICE_SESSION_ENABLED`] → 已登记为范围外，留给后续「L2 落地或降级」决策一并处理。
