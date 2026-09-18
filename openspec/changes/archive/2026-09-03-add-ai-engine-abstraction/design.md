## Context

动机见 proposal.md - Why。当前状态（已核对源码）：

- `apps/ai_assistant/agent_scope/` 内部分层已较好：`config.py`（dataclass + 提示词）、`model.py`（create_model/build_agent + DeviceExecution/PlatformTask）、`workflow.py`（planner→executor↔verifier）、`tools.py`（平台工具函数 + AgentScope 包装混合）。
- 耦合在 `views_drf.py`：直接 `from .agent_scope.workflow import …`、自己 `asyncio.run` + `threading.Thread`、返回松散 dict，device_control 结果 `result.get("assertion","")` 恒空。
- 设备引擎 `engines/`（L1c）已有「Protocol + registry + 可替换插槽」先例，可复用其范式。

## Goals / Non-Goals

**Goals:**

- 建立 `ai_engines/` 协议层（纯类型，零 django/apps 依赖）与注册表（fail-fast）。
- 把 `agent_scope` 框架专用代码迁入 `ai_engines/agentscope/`，平台工具纯函数留在 Django 层经注入。
- `views_drf.py` 解耦为「engine_adapter + get_ai_engine().run()」，结果归一化修 device_control 恒空。

**Non-Goals:**

- 不新增网络通道（进程内调用，遵守通道封闭集合；SSE 保持已移除）。
- 不改 `AITask` 表、`/api/ai/tasks/submit` 契约、前端任何页面。
- 不改运行时路由逻辑（三模型 workflow 行为等价）。

## Decisions

1. **协议 = 进程内 Python `Protocol` + 强类型 DTO**（对齐 `engines/base.UiEngine`），非网络 RPC。
2. **落点 = 新建顶级 `ai_engines/`**，对称 `engines/`。
3. **工具归属 = 工具函数留 Django 层，经 `TaskRequest.tools` 注入**；引擎零 apps 依赖，通用可复用。
4. **引擎接口 = 阻塞 `run()`**（引擎内部 `asyncio.run`）；Django 用 `threading.Thread` 调度，屏蔽框架 async 特性。
5. **结果归一化 = 统一 `TaskResult`**，`summary` 落 `AITask.result`（修 device_control 恒空）。
6. **密钥边界 = Django 解密后传 `ModelSpec.api_key`**，引擎不碰 Fernet。
7. **引擎选择 = `settings.AI_ENGINE`** 默认 `"agentscope"`，对称 `DEVICE_ENGINE`。

## 模块防火墙自检

```
apps/ai_assistant(views) ──✅──→ ai_engines.base / registry
apps/ai_assistant(tools)  ──✅──→ 各业务 App api.py（读放开写收敛）
ai_engines/agentscope     ──❌──→ apps.* 内部实现 / django models 写
ai_engines/agentscope     ──✅──→ AgentScope 第三方库（唯一可触碰框架的层）
apps/*（其他 App）        ──❌──→ ai_engines/agentscope 内部实现
```

## Risks / Trade-offs

- [import 链重连（迁移）] → 逐函数核对只读/自动放行元数据；先固化 `workflow.run()` golden 样例，迁移后逐条比对。
- [引擎零 apps 依赖被破坏] → 若引擎实现需新数据，经 `TaskRequest` 扩展字段或工具注入，禁反向 import apps。
- [api_key 泄露] → 仅 Django 侧解密，`TaskRequest` 不进日志，结果不暴露 Key。
- [行为回归] → 迁移不改行为；真机两条线路各跑通 ≥1 次 + 单测对齐。

## Migration Plan

按 tasks.md §1~§7 顺序：协议层 → 工具剥离 → 迁移 agent_scope → Django 解耦 → 开发工具跟随 → 门禁文档 → 回归验收。每阶段可独立验证、可回滚（保留 `agent_scope/` 到 §4 解耦完成后再删）。
