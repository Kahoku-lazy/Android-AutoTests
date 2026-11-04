## Context

现状（动机见 proposal.md - Why）：

- `platform_run._drive_real` **每条用例**建一次 `build_executor()` / `build_verifier()`，`AgentSOPWorkflow` 在 `run_workflow` 里把同一对实例传给每个 `SOPStep(executor=..., verifier=...)`；历史存在 `agent.state.context`（list），只增不减。
- 用例资产 `CaseStep` 只有 `action` / `expected`；`SOPStep` 的 `subject`（执行者动作）与 `description`（验收标准）互斥注入，这是既有硬约束。
- 验收提示词写死「系统提示词末尾附有日志关键词表（关键词 → 功能点）」，但引擎侧没有这张表；全量目录实际在 `backend/config/device_log_keywords.json`（67 关键词 / 56 功能点），只服务前端工具箱表格。
- 实测基线（TASK-178）：580s、¥1.2542、239 万输入 token；单次调用输入 8.7K（step1）→ 28.7K（step5）；验收在 step2 盲猜 13 次关键词。

## Goals / Non-Goals

**Goals:**

- 每个 SOP 步骤用独立角色实例起步，跨步不继承对话上下文。
- 用例步骤可携带 `anchor` / `log` 两项结构化补充，**只注入当前步**，且不破坏 subject/description 互斥。
- 验收拿得到按型号的关键词目录，关键词来源可追溯（步骤证据 > 关键词表），不再连续盲猜。
- 回归 TASK-178 同一用例：仍 5 步通过，耗时/费用明显下降。

**Non-Goals:**

- 不做前端用例编辑器的 `anchor` / `log` 字段（引擎侧先支持解析，编辑器另开变更）。
- 不迁移 `backend/config/device_log_keywords.json`（前端工具箱仍读它）。
- 不改 SOP 状态机、判决语义、事件折叠、计费规则。
- 不引入 RAG / 知识库注入。

## Decisions

### D1 角色工厂 + 装配时每步各建一对实例

`AgentSOPWorkflow` 构造参数由「executor / verifier 实例」改为「executor_factory / verifier_factory」；`run_workflow` 在构造 `SOPStep` 列表时对每步调用一次工厂（`executor=executor_factory()`）。重试发生在 `SOPStep` 内部，天然复用该步实例，符合「同一步重试不重建」。
**备选**：① 复用实例 + `executor.state.context.clear()`（现状 `state.context` 是 list，一行可行，但依赖 agentscope 内部结构，升级会断）；② 惰性代理（首次 `reply_stream` 时才构造，省启动开销但多一层包装、事件里的 `name`/`model` 需转发）。选①之外的简单方案：提前构造 10 个实例预计 1~2s，占 580s 的 0.3%，不值得引入包装层。

### D2 结构字段只在 workflow 边界拼字符串

不修改 agentscope 的 `SOPStep`（外部依赖），也不引入新的事件类型。做法是：

```python
subject   = action + ("\n\n【本步页面锚点】\n- 页面：…\n- 入口：…" if anchor else "")
description = expected + ("\n\n【本步日志证据】sku=… port=… keyword=…" if log else "")
```

这样继续满足「执行者看不到验收标准、验收者看不到动作」，且旧用例（无 anchor/log）拼出来的字符串与现在逐字相同。

### D3 `CaseStep` 增加两个可选字段，校验失败返回原因

`CaseStep` 增 `anchor: Mapping[str, str] | None`、`log: LogEvidence | None`（dataclass：`sku` / `port` / `keyword`）。`parse_cases` 保持「返回 (items, reason) 不抛异常」的既有风格：

- `anchor`：必须是映射，键只允许 `page` / `entry` / `target`，值转字符串且长度 ≤ 120；出现未知键 → 拒绝并说明。
- `log`：必须是映射，`sku` 非空、`port` 为正整数、`keyword` 非空；缺项 → 拒绝并说明。
- 两者都缺 → 行为与现在完全一致。

### D4 关键词两视图，用一致性测试兜住重叠

- **全量目录**（展示用，不改）：`backend/config/device_log_keywords.json`。`device-log-keyword-catalog` 要求「看到的就是正在用于判定的那张表」，所以引擎视图里的每个关键词都必须在全量目录里登记。
- **判定视图**（注入用，新增）：`engines/agents/config/data/log_keywords/<SKU>.md`，按「功能点 → 关键词」手写，先落 `H6810.md`（内容取自 TASK-178 实测命中：`timer_configs_set_success` / `awaken_configs_set_success` / `sleep_configs_set_success` 等）。
- `tests/graybox/unit/test_log_keyword_catalog.py`：解析 md 里出现的每个关键词，断言都存在于全量目录；反之不要求（按型号裁剪是允许的）。
- **备选**：把 JSON 搬进 engines 让 backend 读（同源，但要动前端工具箱的读取路径与 `settings.py`，爆炸半径大）；或每步注入全量 67 条（约 3K token/步，噪声大且与「按型号」诉求不符）。

### D5 注入预算

| 块 | 大小 | 频次 |
|---|---|---|
| `【本步页面锚点】` | ≤ 4 行（约 60 token） | 每步 × 执行者 |
| `【本步日志证据】` | 1 行（单关键词 ≈ 30 token；多关键词多一行提示） | 每步 × 验收者 |
| `【本步关键词表】` | H6810 预计 ≤ 40 行（约 500 token） | 每步 × 验收者 |

单步新增 ≤ 600 token；相对每步 15–29K 的输入可忽略。

**多关键词**：`log` 支持 `keyword`（单个）或 `keywords`（列表，≤ 6）两种写法，二者互斥。列表按顺序注入，验收逐个调用 `check_device_log`；**重复项表示该关键词要命中多次**（例如开灯 + 关灯两个 `switch_*` 事件、两次亮度设置）。这比新增 `count` 字段少一个概念，也不需要工具层改动。上限 6 是为了避免一步把整张表塞进提示。

### D6 缺目录时降级，不中断

`config/log_keywords.py` 的 `load_log_keywords(sku) -> str` 在文件缺失/不可读时返回空串；workflow 边界把「该型号关键词目录缺失」写进验收提示，验收按提示词要求退回截图核对。目录里出现全量目录未登记的关键词时，该条被剔除（见 D4）。

### D7 事件与计费不受影响

角色名（`ui_executor_role` / `ui_verifier_role`）与模型由工厂决定、保持不变，事件流按名字聚合与计费口径都不变；每步新建实例的 usage 仍写进同一任务。

### D8 删除「最近 3 步保留截图」需求

现存代码里没有独立的跨步裁剪实现（实际由 `ContextConfig.max_image_num=5` 与上下文压缩兜底）。每步隔离后跨步上下文不存在，该需求没有对象，故在 delta 里 REMOVE 并说明迁移。

### D9 开场上下文每步重放（TASK-179 实测暴露）

每步新建实例后，**开场输入只进第一步**的旧语义会让第 2 步起丢掉设备 serial：TASK-179 里第二步的验收拿不到 serial，去试 `emulator-5554` / `127.0.0.1:7005` 全部 offline，判决直接判「无证据」。因此装配时把开场上下文（至少设备 serial）**重放进每一步**的 subject 与 description。
代价：每步多约 30 token；换来新实例不必猜设备号。

### D10 关键词表按「步 → 用例标题」两级兜底（TASK-179 实测暴露）

旧用例资产没有 `log` 字段，若只按 `log.sku` 取表，第 2 步就完全没有关键词来源，加上新提示词「两者都没有就判不通过」，等于把旧用例判死。因此：步上有 `log.sku` 用步上的；没有就用**用例标题里识别出的型号**（`[A-Z]\d{3,5}`，如「H6810 定时功能测试」→ `H6810`）取同一份表。此时只给表、不给具体关键词，验收按功能点选一条。

### D11 执行者交卷前必须停在结果页（TASK-179 实测暴露）

TASK-179 第二步的执行者先按返回键回到详情页，再交 handover；验收随后截图看到的是详情页，自然判「看不到定时列表」。这是执行顺序问题，不是验收太严：在执行提示词里加一条硬约束——交卷前停在本步结果页并先截图留证，返回/退出排在判定之后。

### D12 验收按断言类型选择主证据

判定标准本来就分两类，旧提示词却要求「一律先截图」，于是日志型断言会因为页面已经离开而额外判负（TASK-179 第一步就吃过这个亏）。改成分流：

- **日志型**（结果要求「设备日志返回 / 日志出现 / 日志成功」）：以日志为唯一判据，命中即通过，**不必截图**，也不因页面已离开而判失败；
- **页面型**（结果要求「页面显示 / 列表里出现 / 开关为开启态」）：以截图为主要判据，**不要调用日志工具**；
- **混合型**：两类都要核对，缺一类判不通过并写清缺哪一类。

这样做还有一个副作用是省钱：页面型步骤不再顺手查一次日志，日志型步骤不再为了"再确认一下"多截一张图。断言里没写日志的，一律按页面型处理，避免模型自行扩大取证范围。

## 模块防火墙自检

- `engines/**` 仍零 `django` / `apps.*` 导入；新增的 `config/log_keywords.py` 只读 `engines/agents/config/data/` 下的自有文件。
- 一致性测试在 `tests/` 层读 `backend/config/device_log_keywords.json`，属于测试允许的读取，不构成 engines → backend 依赖。
- 不新增写库路径、不改数据库结构、不改前端；无跨 App 写操作。

## Risks / Trade-offs

- [每步新建实例丢失「当前停在哪个页面」] → 每步多 1 次截图确认（约 +2~4s、+2K token）；若某步强依赖上一步页面，可在 `anchor.entry` 里写明「从 X 页进入」。
- [新实例丢掉开场上下文里的设备 serial] → D9 逐步重放；TASK-179 已实测该问题会直接把验收打到「无证据」。
- [旧用例没有 `log` 导致关键词断供] → D10 用标题型号兜底；无型号时才退回「缺表、按截图核对」。
- [执行者交卷前离开结果页] → D11 提示词硬约束；`test_role_prompt_guardrails.py` 守护。
- [关键词视图与全量目录漂移] → 一致性测试；md 里写错关键词会直接让测试红。
- [10 个实例的启动开销] → 实测；若超过 3s，退化为惰性构造（记录为备选方案 D1②）。
- [验收变严格：表里没有就判不通过] → 用 TASK-178 原用例回归，确认 5 步仍通过；若某步因目录缺条目被卡，补目录而不是放宽提示词。
- [用例资产新增字段未被编辑器写入] → 旧编辑器保存时不带这两个键，解析为 None，行为不变；新字段由引擎侧或脚本写入。

## Migration Plan

无数据迁移、无部署顺序要求。按 3 个可独立回滚的提交推进：① 结构字段 + 步骤简报；② 关键词目录 + 注入 + 提示词；③ 每步隔离。每步都能单独 revert，且旧 YAML 一直兼容。

## Open Questions

- 前端用例编辑器何时暴露 `anchor` / `log` 字段？（本期不做；引擎侧先解析，编辑器后续按需加，不阻塞。）
