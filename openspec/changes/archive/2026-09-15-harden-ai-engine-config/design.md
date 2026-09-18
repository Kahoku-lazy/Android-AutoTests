## Context

动机见 `proposal.md` - Why。方案所需现状约束：

- A1 契约（`engines/ai/base.py`）只允许标准库类型，`ModelSpec` 字段为 provider / model_name / api_key / base_url；引擎层不得 import `django.*`、`apps.*`（`engines/__init__.py:6`）。
- A1 已有异常类型 `ConfigurationError`（`engines/ai/registry.py:19`），语义为「引擎配置错误」。
- A2 的 `build_request` 是 HTTP 链路唯一装配入口，但两个管理命令（`model_test.py:33-35`、`ui_pipeline.py:14-16`）绕过它直接构造引擎配置 —— 因此 A3 侧的自校验不可省。
- 装配异常已有兜底：`views_drf.py:840-847` 的 `except Exception` 会把异常落成任务失败终态与日志，A2 抛错无需新增捕获路径。
- 写入侧已约束 provider：`serializers.py:54,78` 用 `VALID_PROVIDERS` 拦截非法值，风险只来自历史数据行。

## Goals / Non-Goals

**Goals:**

- 把「配置非法」的发现时机从工作流中段提前到装配期，且错误文案可定位到角色与字段。
- 让 provider 合法性与 base_url 只由一处定义，并让两侧（Django / 引擎）的 provider 集合可被一条测试断言守护。

**Non-Goals:**

- 不改 A1 契约（`ModelSpec` 字段与 `TaskRequest` 结构不变）。
- 不收窄 `PROVIDER_DEFAULTS` 的 provider 集合（`anthropic` / `gemini` 走 OpenAI 兼容路径事实可用）。
- 不合并 `agentscope/billing.py` 与 `apps/ai_assistant/deepseek_billing.py` 的计费函数（属报告 P1，另一单）。
- 不改前端、不改 DRF 路径与信封、不加数据库迁移。

## Decisions

### D1 provider→凭证类 的映射留在引擎侧，不从 A2 透传

- 决策：A2 只负责「provider 合法性 + base_url 解析」，A3 保留「provider → 凭证类」的显式分支。
- 理由：`DeepSeekCredential` / `DashScopeCredential` / `OpenAICredential` 是框架概念；若由 A2 决定并填入 `ModelSpec`，框架词汇会漏进 A1 契约，与文档 A3 的「不把框架类型漏进 A1」相悖。
- 备选：给 `ModelSpec` 增 `credential_type` 字段 —— 否决（污染 A1 契约）；把 `PROVIDER_DEFAULTS` 当唯一真相源由 A3 查表 —— 否决（引擎不得 import `apps`，A3 拿不到该表）。
- 代价：provider 集合客观上存在两处描述。缓解见 D6（一致性测试）。

### D2 删除 `provider_registry.credential_type`

- 决策：删除该键；`PROVIDER_DEFAULTS` 收敛为「provider → base_url」。
- 理由：全仓唯一引用是定义处（零消费方），保留会继续暗示「A2 决定凭证类」，与 D1 冲突。

### D3 A3 兜底改为显式白名单 + 抛错

- 决策：`create_model` 保留 `deepseek`（含 vision 特例）与 `dashscope` 两个显式分支；其余收窄为 OpenAI 兼容白名单常量 `SUPPORTED_PROVIDERS`，白名单外抛 `ConfigurationError`（复用 A1 异常类型）。
- 理由：白名单与分支同文件邻接，既是实现也是「引擎能处理哪些 provider」的可测事实来源；复用 `ConfigurationError` 避免新增异常类型。
- 备选：新定义 `EngineConfigError` —— 否决（无收益）；A3 直接 import `apps/ai_assistant/provider_registry` —— 否决（违反引擎零 apps 依赖）。
- 依赖方向自检：`model.py → engines/ai/registry.py` 同属 L1c 引擎层；`registry.py` 只在函数内用 `importlib` 加载实现（`registry.py:43-52`），无循环导入。

### D4 A2 校验的落点与异常类型

- 决策：在 `engine_adapter.py` 内新增 `_validate_route_cfg()` 与设备串校验；抛 `ValueError`，文案为中文且指明角色/字段/合法集合，不含密钥。
- 理由：异常由 `views_drf.py:840-847` 兜底成 `执行异常: {exc}` 落 `AITask.result`，用标准异常即可，无需新增类型与捕获点。
- 备选：`django.core.exceptions.ValidationError` —— 否决（属表单/DRF 语义）；`ConfigurationError` —— 否决（那是引擎侧词汇，Django 侧不该为此 import 引擎包）。

### D5 无设备串时在装配期报错

- 决策：`task.device_serial` 与在线设备都取不到时抛错，不再返回空串。
- 理由：`device_control` 线路必须落在具体设备上；serial 在装配时一次性解析，工作流不会二次分配，空串只会让失败推迟到工具层且文案模糊。
- 备选：保留空串 —— 否决（不存在「先提交、设备后到再分配」的实现）。

### D6 用一致性测试守护两侧 provider 集合

- 决策：A3 暴露模块级常量 `SUPPORTED_PROVIDERS = {"deepseek", "dashscope"} | OPENAI_COMPATIBLE_PROVIDERS`；测试断言它与 `VALID_PROVIDERS` 相等。
- 理由：引擎不得 import `apps`，共享代码不可行，唯一低成本的一致性手段是断言；常量与分支同处一文件使漂移会立刻被测试发现。
- 备选：测试内硬编码 6 个 provider 名 —— 否决（新增 provider 时测试不会提醒，反而固化）。

## 模块防火墙自检

- 跨 App import：无。本单只改 `apps/ai_assistant` 内部两个文件，未新增任何跨 App 依赖。
- 写库：无。全部为装配期只读校验；异常路径由既有 `views_drf` 兜底写失败终态，不经本单新增的写入口。
- 引擎边界：`engines/ai/agentscope/` 仍不 import `django.*` / `apps.*`；新增依赖仅为同层的 `engines/ai/registry.ConfigurationError`。
- 前端/仪表盘：不涉及。
- 新增文件落层：测试文件落 `tests/graybox/unit/`；无新增源码文件。

## Risks / Trade-offs

- [存量 `route_configs` 含集合外 provider 或空模型名 → 变更后这类智能体立即无法执行] → 实施第一步做只读核查（`AIAgent.objects.values_list("route_configs", flat=True)` 去重 provider / 检查三角色 model_name），发现异常先订正配置行，再合并代码。
- [用户可见路径变化：由「运行中失败」变为「提交后立即失败」] → 提交接口仍在后台线程执行、仍返回 200，前端表现不变；错误文案为中文且可定位，落 `AITask.result`。
- [`SUPPORTED_PROVIDERS` 常量与 `create_model` 分支漂移] → 常量与分支同一文件同一函数邻接，另有 D6 一致性测试守护。
- [dashscope 传 `base_url` 后链路若确实不支持，会由「静默丢弃」变为报错] → spec 已覆盖两种走向：生效或显式报错；实测不支持时改为 A2 对该 provider 拒绝自定义地址。
- [A3 为异常类而 import A1 的 registry] → 属同层依赖且无环；若评审认为不当，备选是把 `ConfigurationError` 上移 `base.py`（会改 A1 契约，本单不做）。

## Migration Plan

1. 只读核查存量配置（无写库）。
2. 按 `tasks.md` 顺序改 A2 → A3 → 测试。
3. 验证命令：`python manage.py check` · `ruff check` + `ruff format --check`（相关路径）· `pytest tests/graybox/unit -q`。
4. 无数据库迁移、无 API 契约变更、无前端变更；回滚 = revert 本次提交（纯代码，无数据副作用）。

## Open Questions

（实施后已定论，保留结论供评审回溯）

- dashscope 自定义 `base_url`：**支持**。框架的 `DashScopeCredential` 自带 `base_url` 字段（默认 dashscope 兼容端点），可直接承接；已按「非空才传、空则用框架默认」实现，并有单测断言不丢弃。无需改为 A2 拒绝。
- 「无设备任务」：**当前无此用法**。serial 只在装配时一次性解析、工作流不二次分配，故按装配期报错处理；若将来需要「设备离线先排队」，改法是把它挪到提交入口做前置校验，spec 的 MUST NOT 仍然成立。
