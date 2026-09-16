# 报告：AgentScope 代码核对与分层分析

> **对照文档**：`dev_docs/05-开发与测试/设计方案与报告/设计方案-AgentScope设计系统分层.html`
> （该文件未入库：`.gitignore:121` 的 `dev_docs/**/*.html` 将其忽略；文件 mtime = 2026-09-14 17:57）
> **核对基线**：HEAD `4eadaab8`（2026-09-15 14:55）；工作区脏文件含 `apps/ai_assistant/rag_service.py` 等
> **核对方式**：逐文件通读 + 全仓 grep 交叉验证；结论一律给出 `文件:行`，行数为 `split("\n")` 实测值

---

## 一、结论摘要

1. **分层坐标成立**。A0–A5 六层与代码实际结构吻合：A1 协议在 `engines/ai/base.py` + `registry.py`，A2–A5 全部落在 `engines/ai/agentscope/`，P1/P2 归属基本正确。
2. **文档 §二「现状断层」8 条中**：**2 条已被修复**（陈旧路径、遗留服务配置，由 `c14527d3` 于 2026-09-15 14:54 处理）、**1 条数字不成立**（`ai-*` spec 是 10 个，不是 12 个）、**5 条成立**。
3. **「只允许 `model.py` / `tool_wrapper.py` 碰框架」在 `engines/` 侧实测成立**；**「apps/ 零命中」不成立** —— `rag_service.py` 有 **10 处** `agentscope.*` 直连，比文档写的 2 处更严重。
4. **文档遗漏 6 个真实分层缺口**（见第四节）：`credential_type` 死字段、dashscope `base_url` 被丢弃、A2 无 `route_configs` 校验、A5 权限 ASK 分支不可达、RAG 泄漏范围被低估、A2/A3 职责交叉。
5. **「换引擎只改一行」当前不成立**（与文档结论一致）；但文档「其余五层都实现在框架侧」的表述不准：**A2 的一半（`engine_adapter.py` + `provider_registry.py`）在 Django 侧**，A0 的开关也在 Django 侧。

---

## 二、实测分层与真实调用链

| 层 | 归属文件（实测行数） | 框架 import | 实测结论 |
|----|--------------------|------------|---------|
| A0 | `config/settings.py:184-187`（AI_ENGINE）、`.env.example:47` | 无 | `config/agentscope_config.py` **已不存在**（`c14527d3` 删除） |
| A1 | `engines/ai/base.py`(81)、`registry.py`(77) | 无 | 零 `django.*`/`apps.*`；未知名/不可导入/构建失败三路 fail-fast 均实现 |
| A2 | `apps/ai_assistant/engine_adapter.py`(72)、`provider_registry.py`(88)、`engines/ai/agentscope/engine.py`(72)、`config.py`(170) | 引擎侧无；Django 侧有 | **A2 横跨两侧**，是分层坐标的模糊点 |
| A3 | `engines/ai/agentscope/model.py`(662) | 有（18-28 行） | 单文件承载 5 种职责（提示词/模型工厂/角色基类/轨迹解析/截图提取） |
| A4 | `workflow.py`(709)、`evidence.py`(56) | **无** | 实测 `workflow.py` 只依赖 pydantic + 同包，零框架 import，与文档一致 |
| A5 | `tool_wrapper.py`(100) + `apps/ai_assistant/tools.py`(447) + `skills_catalog.py`(214) + `views/tool_gateway.py`(240) | 有（10-13 行） | 工具真相源在 Django 侧，包装在引擎侧 |
| P1 | `usage.py`(59)、`billing.py`(68)、`apps/ai_assistant/deepseek_billing.py`(108) | 无 | 价目 + 别名表 + 峰谷规则**三份重复** |
| P2 | `rag_service.py`(374)、`llm_semantic.py`(52) | **有（apps 直连）** | 唯一绕过 A1 的框架直连点 |

**真实调用链（HTTP 链路）**

```
views_drf.py:817-819
  engine_adapter.build_request(task, agent)      ← A2（Django 侧）
      解密 key + 解析 base_url + TOOLS→ToolSpec + skill 目录
  registry.get_ai_engine(settings.AI_ENGINE)     ← A1
  AgentScopeEngine.run(req)                      ← A2（引擎侧）
      _to_model_config ×3 → DeviceExecutionConfig
      build_device_models → PlannerRole / ExecutorRole / VerifierRole   ← A3
      asyncio.run(DeviceExecutionWorkflow.run)                          ← A4
          Plan → 每步 Exec↔Verify ≤ max_loops → on_progress 回调        ← A5 工具经 build_toolkit
  → TaskResult → views_drf.finalize_task
```

---

## 三、文档断言逐条核对

### 3.1 §二 现状断层（8 条）

| # | 文档断言 | 实测 | 判定 |
|---|---------|------|------|
| 1 | A0 陈旧路径：`config/agentscope_config.py:61` 与 `views/tool_gateway.py:9` 指向不存在的 `apps/ai_assistant/agent_scope/` | `config/agentscope_config.py` 已被 `c14527d3` 整体删除（删除前第 61 行注释正是「Skill paths have been moved in-process to apps/ai_assistant/agent_scope/」）；`views/tool_gateway.py:9` 现为空行，无 `agent_scope` 引用 | **当时成立，现已修复** |
| 2 | A5 框架直连泄漏：`rag_service.py:23-24` 是全仓引擎侧之外唯一的框架 import；通道③测试未覆盖 | 直连确实只在 `rag_service.py`（其余 apps 文件 0 命中），但**共 10 处**：23、24、228、229、237、238、245、246、267、283，覆盖 `message`/`rag`/`credential`/`embedding` 四个子模块；`tests/arch/test_channels.py:70-78` 仍只断言目录不存在 | **成立，且实际更严重** |
| 3 | P1 价目双份：`billing.py:11` 与 `deepseek_billing.py:11` 各一份 `DEEPSEEK_PRICING` | 两份 dict 逐字相同（`billing.py:12`、`deepseek_billing.py:10`）；**重复的不止价目**：`_DEEPSEEK_MODEL_ALIASES`、`_DEFAULT_DEEPSEEK_MODEL`、`_PEAK_MULTIPLIER` 也各一份 | **成立（行号偏差）** |
| 4 | A0 遗留服务配置：仍保留 `AGENTSCOPE_SERVICE_{PORT,URL,TITLE,VERSION}` 与 "FastAPI agent service" | 全仓（含 `.env.example`、`config/`）grep `AGENTSCOPE_SERVICE` = **0 命中**；`c14527d3` 删除的 `config/agentscope_config.py` 内容即 `AGENTSCOPE_SERVICE_PORT/TITLE/VERSION` | **当时成立，现已修复** |
| 5 | 接入 · `apps/ai_assistant/AGENTS.md` 实测 0 行 | 文件存在，**0 字节** | **成立** |
| 6 | 通道 SSOT 已收敛（`architecture.md` 已改指 `ARCH-00 §1.4`） | `tests/arch/test_channels.py:3` 已指 ARCH-00 §1.4；但 `apps/AGENTS.md:43,99` 仍写「WS 生产点 = 1 个：编辑锁」，而 `gateway/routing.py:9` 是空表、ARCH-00 §1.4 记 0 个 | **路径已收敛，计数仍有矛盾** |
| 7 | A1 能力 spec 12 个 `ai-*`，仅 `ai-engine-protocol` 有真实 Purpose | `openspec/specs` 下 `ai-*` 共 **10 个**（ai-agent-model-config / ai-agent-routes / ai-device-action / ai-engine-protocol / ai-intent-routing / ai-multi-agent-orchestration / ai-page-flow-capture / ai-platform-task / ai-screen-vision / ai-task-publishing），9 个 Purpose 为 TBD | **方向成立，数字错误（10 非 12）** |
| 8 | A4 待确认：`ai-multi-agent-orchestration` 5 条需求在 engines/apps 内零命中 | engines/ 内 `orchestrat|multi_agent|pipeline` = 0 命中；`intent_code|IntentResult|run_intent` 全仓 `.py` = 0 命中；`route_configs` 现只有 1 条线路（`views_drf.py:176 _ROUTE_KEYS = ("device_control",)`）；`strong_enabled` / `strong_model_name` 只剩模型字段与序列化器，无引擎消费方 | **成立，且可给出结论（见 3.3）** |

### 3.2 §三 验收口径（4 条，文档自称「若落地按此判定」）

| 口径 | 实测 | 判定 |
|------|------|------|
| 换引擎只改一行（settings.AI_ENGINE） | `rag_service.py` 10 处 + `model_test.py:33-35` + `ui_pipeline.py:14-16` 直连具体引擎 | **不成立**（文档自认） |
| 框架 import 白名单：仅 `model.py`/`tool_wrapper.py`，apps 0 命中 | engines 侧成立；apps 侧不成立；且**并无 arch 内容扫描测试**，`tests/arch/test_channels.py` 只查目录 | **engines 侧成立；守护测试缺失** |
| 单份计价 | 见 3.1 #3 | **不成立** |
| 层级可查（新文件都能落进 A0–A5） | 实测所有文件都可落层；`engine_adapter.py`/`provider_registry.py` 属 A2 但不在文档 A2 清单之外的「框架侧」 | **成立** |

### 3.3 回答文档 A4 的「待确认」问题

`ai-multi-agent-orchestration` 描述的「4 套 Harness（意图识别/视觉/推理/强模型）+ `intent_code` 1/2 路由 + 强模型短路开关」**当前代码里没有实现**：

- 意图识别：`intent_code` / `IntentResult` / `run_intent` 全仓 Python 0 命中；
- 4 套 Harness：引擎侧只有单条 `DeviceExecutionWorkflow`（planner → executor ↔ verifier），无 Harness 抽象；
- 「双线路」：`route_configs` 只剩 `device_control` 一条（`views_drf.py:176`、`models.py:29`）；
- 强模型开关：`strong_enabled` / `strong_model_name` 仅存于 `models.py:25-28`、`serializers.py:31-32`、`api.py:168-169`，**引擎与视图均无消费方**；
- `dev_docs/项目笔记/AgentScope/多智能体编排-最终骨架设计.md:41` 自己写明「已移除：`intent` Harness（`IntentResult`/`run_intent`/`route`/`resolve`）」。

**口径建议**：该 spec 属「需求已登记、实现已移除/未落地」。要么按现状改写 spec，要么作为待办立项 —— 但不应把它算作 AgentScope 分层设计的一部分。

---

## 四、文档未覆盖的分层缺口（本次新发现）

### N1 · A2 的 `credential_type` 是死字段，provider→凭证 映射双份且无一致性校验
- `provider_registry.py:58` 返回 `credential_type`，全仓唯一引用就是它自身，**无任何消费方**。
- 真正的 provider→Credential 映射硬编码在 A3：`model.py:217-243`（deepseek→DeepSeek/OpenAI 兼容、dashscope→DashScope、其余→OpenAI 兼容）。
- 后果：`PROVIDER_DEFAULTS` 有 6 个 provider（含 anthropic/gemini/custom），`validate_base_url` 只对已知 provider 做 host 白名单，而 `create_model` 对**未知 provider 一律按 OpenAI 兼容处理、不报错** —— 违反 A1 的 fail-fast 精神。
- 文档「S2 = 加一个 `PROVIDER_DEFAULTS` 条目 + 一个 Credential/ChatModel 分支，干净」低估了改动面：需同时改两处，且无测试保证两者一致。

### N2 · dashscope 分支丢弃 `base_url`
`model.py:233-238`：`DashScopeChatModel(credential=DashScopeCredential(api_key=...))` 未传 `base_url`。而 A2 的 `engine_adapter._model_spec` 对所有 provider 都解析了 base_url —— 为 dashscope 配的自定义地址被**静默丢弃**。

### N3 · A2 缺 `route_configs` 结构校验与设备缺失处理
- `engine_adapter.py:56-61` 用 `(route_cfg.get(role) or {})` 取三角色，缺失角色会生成 `provider="deepseek", model_name="", api_key=""` 的 ModelSpec，直到 A3 建模型或 LLM 调用才失败（且报错点远离故障原因）。
- `engine_adapter.py:42-49` 无在线设备时返回 `device_serial=""`，工作流照常启动，错误留到工具调用阶段。
- 文档把「不做静默回退」只写进 A1，A2 的这两处默认值实际就是静默回退。

### N4 · A5 的权限 ASK 分支在设备执行链路不可达
- `tool_wrapper.py:84-89`：只读 → ALLOW；`auto_allow` → ALLOW；否则 ASK。
- `tools.py:374-391` 中 `read_only=False` 的 6 个工具（acquire/release/device_action/click_ratio/drag_ratio/xpath_action）**恰好等于** `AUTO_ALLOW_TOOLS`（`tools.py:365-372`）→ 当前设备链路只会出现 ALLOW。
- 风险：新增写工具若漏加 `AUTO_ALLOW_TOOLS`，就会走 ASK，而设备执行链路没有人工应答方（框架对该情形的具体行为需另行确认）。文档的 A5 契约「只读/自动放行标记」缺少对应的守护测试。

### N5 · A2/A3 职责交叉：`build_request` 并非 TaskRequest 的唯一装配点
- `on_progress` 由 `views_drf.py:818` 在 `build_request` **之后**赋值；
- `model_test.py:33-35`、`ui_pipeline.py:14-16` 完全绕开 `build_request`，各自构造 `DeviceExecutionConfig`。
- 文档 A2 写「`build_request` 是唯一入口」，只在 HTTP 链路成立。

### N6 · 进度回调的落库实现与「引擎不写库」的边界代价
`views_drf.py:779-805` 的 `persist_task_progress_safe` **每次回调新建线程并 `join(timeout=30)`**；A4 每步结算都回调一次 → 单任务串行等待线程完成（最坏每步 +30s）。这属于「A2 装配 + 接入」边界上的性能与耦合问题，文档的分层清单未覆盖。

### N7 · 引擎层测试覆盖与文档验收口径不匹配
现有 `tests/graybox/unit/`：`test_ai_workflow_progress.py`（只测 `_progress_payload` / `_emit_progress` 纯函数）、`test_ai_tool_gateway_auth.py`、`test_deepseek_billing.py`、`test_ai_startup_recovery.py`。**没有**覆盖 registry fail-fast、`ModelSpec→ModelConfig`、`build_toolkit`/权限、三角色装配、`_parse_json` 容错的测试。文档 §三 写「由 arch 测试断言」，而该断言测试并不存在。

---

## 五、文档自身的准确性问题

1. **行数漂移**（实测 / 文档）：`rag_service.py` 374/354、`llm_semantic.py` 52/44、`deepseek_billing.py` 108/102、`evidence.py` 56/49、`billing.py` 68/64、`usage.py` 59/57、`skills_catalog.py` 214/212、`tool_gateway.py` 240/237、`model.py` 662/663、`workflow.py` 709/711。其余（`base 81`、`registry 77`、`engine 72`、`config 170`、`tool_wrapper 100`、`engine_adapter 72`、`provider_registry 88`、`tools 447`）与实测一致。
2. **时效性**：文档是 2026-09-14 17:57 的快照；次日 14:54 的 `c14527d3` 恰好删掉了它点名的 `config/agentscope_config.py` 与 `AGENTSCOPE_SERVICE_*`。文档 §四「结论」因此已部分过期（两条断层已消失）。
3. **「12 个 ai-* spec」应为 10 个**（见 3.1 #7）。
4. **「通道 SSOT 已收敛」只对了一半**：引用路径已收敛，但 `apps/AGENTS.md:43,99` 的 WS 生产点数（1）与 `gateway/routing.py`（0）、ARCH-00 §1.4（0）仍冲突。
5. **「其余五层都实现在框架侧」表述不准**：A0 全在 Django 侧，A2 一半在 Django 侧（`engine_adapter.py`、`provider_registry.py`）。更准确的说法是「A2–A5 的**引擎内部**实现在框架侧；A0 与 A2 的**装配入口**在 Django 侧」。
6. `apps/ai_assistant/AGENTS.md` 0 字节：文档点出后仍为空，是 8 条断层里唯一「零成本可修」且尚未修的。

---

## 六、建议（按优先级）

> 落地方式：按 `AGENTS.md` 的强制要求，全部走 OpenSpec 轻量流程（一事一 change，完成后 archive）。下表按「一个 change 一件事」切分。

### P0 · 先消除静默行为 —— change「harden-ai-engine-config」✅ 已于 2026-09-15 落地

**P0-1 provider→凭证 映射单份化 + 未知 provider fail-fast**
- 现状：`provider_registry.py:58` 的 `credential_type` 无人消费（唯一引用是它自身）；真实映射硬编码在 `model.py:217-243`；`create_model` 的兜底分支把**任何未知 provider 当 OpenAI 兼容**，不报错。
- 建议：让 A2 决定凭证类型、A3 只做「凭证类名 → 构造」，使 `PROVIDER_DEFAULTS` 成为唯一真相源；`create_model` 收到未知 provider 时抛错（文案含 provider 名与合法集合）。
- **前置核查（必做）**：`serializers.py:54,78` 已用 `VALID_PROVIDERS` 把住入口，但历史 DB 行可能存有集合外的 provider。改为 fatal 之前，先把 `ai_agent.route_configs` 中出现过的 provider 去重查一遍；有集合外的值就先数据订正，否则会把存量智能体变成不可执行。
- 验收：新增单测「未知 provider → ConfigurationError」+「deepseek / dashscope / openai 三分支构造成功」。
- ✅ 已落地：`provider_registry.py` 删除 `credential_type`、`PROVIDER_DEFAULTS` 收敛为 provider→base_url；`engines/ai/agentscope/model.py` 兜底收窄为 OpenAI 兼容白名单并对未知 provider 抛 `ConfigurationError`。**实施时调整了上述建议**：凭证类映射留在 A3（`DeepSeekCredential` 等属框架概念，不进 A1 契约），A2 只负责合法性与 base_url —— 见该 change 的 `design.md` D1。

**P0-2 并入同一 change：dashscope 传递 `base_url`（2 行）**
- `model.py:233-238` 未把 A2 解析出的 base_url 传给 `DashScopeChatModel`。
- 若判定「dashscope 就是不支持自定义地址」，应在 A2 明确拒绝并报错 —— 现状是**解析后丢弃**，最难排查。
- ✅ 已落地：dashscope 分支传递 `base_url`（为空时保留框架默认端点），单测断言凭证入参保留自定义地址。

**P0-3 A2 必填校验（`engine_adapter.py`）**
- 现状：`:56-61` 用 `(route_cfg.get(role) or {})`，缺失角色会生成 `provider="deepseek", model_name="", api_key=""`；`:42-49` 无在线设备时返回 `""`。
- 建议：加 `_validate_route_cfg()`：`device_control` 必须存在，三角色 `model_name` 与可解密 `api_key` 非空；缺失即抛含「缺哪个角色/字段」的异常。无在线设备且 `task.device_serial` 为空时明确报错。
- 无需新增捕获路径：`views_drf.py:840-847` 已有兜底，会把异常落成用户可读的失败 message。
- 验收：单测覆盖「缺 planner」「model_name 为空」「无在线设备」三种输入。
- ✅ 已落地：`engine_adapter.py` 新增角色 / provider / 设备串三类装配期校验（`_model_spec` + `_resolve_device_serial`）；前置只读核查实测 1 个智能体、provider 全为 `deepseek`、零问题，故不存在存量不可执行风险。

### P1 · 三个独立 change

| change | 动作 | 落点 | 验收 |
|--------|------|------|------|
| `arch-agent-scope-import-whitelist` | 在 `TestAgentScopeChannel` 增内容扫描：`apps/**/*.py` 不得出现 `from/import agentscope`，白名单显式登记 `apps/ai_assistant/rag_service.py`，并在测试里注明白名单的到期条件（收口后删除） | `tests/arch/test_channels.py:70-78` | 新增 1 条测试；故意加一行 import 应失败 |
| `deepseek-pricing-single-source` | 新增 framework-free 的 `engines/ai/billing.py` 作为唯一真相源（价目 + 别名表 + 峰谷规则），`engines/ai/agentscope/billing.py` 与 `apps/ai_assistant/deepseek_billing.py` 都改为引用它 | `billing.py:12-29`、`deepseek_billing.py:10-35` | `pytest tests/graybox/unit/test_deepseek_billing.py` 全绿；单一价目表 |
| `ai-app-boundary-doc` | 补写 0 字节的 App 约束（引擎边界白名单、任务发布链路、工具网关 `X-Internal-Token` 鉴权、`AUTO_ALLOW_TOOLS` 约定、关单 delta） | `apps/ai_assistant/AGENTS.md` | 文件非空且被 `apps/AGENTS.md` 索引引用 |

- **价目收敛的方向约束**：依赖方向只能是 `apps → engines`。放在 `engines/ai/billing.py`（而非 `engines/ai/agentscope/billing.py`）可避免 Django 为计价去 import AgentScope 包。
- **不要强行合并两个计费函数**：`model_cost(provider, ...)`（非 deepseek 返回 0）与 `deepseek_cost(input, output, cache, ...)` 语义不同，保留两个薄包装、共享一张价目表即可。

### P2 · 文档与 spec 口径

| 动作 | 落点 | 说明 |
|------|------|------|
| 同步文档事实 | 设计方案 HTML | 行数（10 处漂移）、`ai-*` spec 10 个而非 12、两条断层已被 `c14527d3` 修复、「其余五层都在框架侧」改为「A2–A5 的引擎内部实现在框架侧；A0 与 A2 的装配入口在 Django 侧」 |
| 修 `apps/AGENTS.md` WS 计数 | `apps/AGENTS.md:43,99` | 仍写「1 个：编辑锁」，与 `gateway/routing.py:9`（空表）和 ARCH-00 §1.4（0）冲突 |
| 给 HTML 加指针 | 设计方案 HTML 末尾 | `dev_docs/**/*.html` 被 gitignore，注定不随代码演进；建议结论段指向本报告 md，避免二次漂移 |
| 收口 spec | `openspec/specs/ai-multi-agent-orchestration`、`ai-intent-routing` | 二选一：改写为现状（单线路 + 三角色 + `strong_enabled` 仅存字段），或立待办并保留 TBD 标记 |

### P3 · 新增守护测试

- `TOOLS` 中 `read_only=False` 的集合必须等于 `AUTO_ALLOW_TOOLS`（`tools.py:365-391`，当前恰好成立）。这样新增写工具时会强制作者显式决定放行策略，避免走到无人应答的 ASK 分支（`tool_wrapper.py:84-89`）。

### 不建议现在做

1. **不要把 RAG 下沉到 `engines/ai/agentscope/`**：`tests/arch/test_channels.py:77-78` 明令禁止该目录下新增 `adapters/`/`rag/`，且与 A5「RAG 属 Django 侧集成」口径冲突。正确做法是登记白名单 + 收敛为单一薄适配点。
2. **不要合并 `model_cost` 与 `deepseek_cost`**：语义不同，收益低于回归风险（见 P1 说明）。
3. **不要在本次收窄 `PROVIDER_DEFAULTS`**：anthropic/gemini 走 OpenAI 兼容路径事实可用，收窄会让现有配置失效；本次只加「未知 provider 报错」。

---

## 附：核对证据（关键命令行）

```
git log --all --format='%h %ci %s' -- config/agentscope_config.py
  → c14527d3 2026-09-15 14:54:27 chore(config): config / gateway / ...   （删除该文件）
git show c14527d3 -- config/agentscope_config.py
  → -PORT/TITLE/VERSION = getattr(settings, "AGENTSCOPE_SERVICE_*")
grep -r "AGENTSCOPE_SERVICE" .            → 0 命中
grep -rn "^from agentscope" apps/         → rag_service.py ×10（23,24,228,229,237,238,245,246,267,283）
grep -rn "credential_type" .              → 仅 provider_registry.py:58 定义处
grep -rn "intent_code|IntentResult|run_intent" .   → 仅一份历史设计笔记
ls openspec/specs                         → ai-* 共 10 个
node 行数实测：base 81 · registry 77 · engine 72 · config 170 · model 662 · workflow 709
              tool_wrapper 100 · usage 59 · billing 68 · evidence 56
              engine_adapter 72 · provider_registry 88 · tools 447 · skills_catalog 214
              rag_service 374 · tool_gateway 240 · deepseek_billing 108 · llm_semantic 52
```
