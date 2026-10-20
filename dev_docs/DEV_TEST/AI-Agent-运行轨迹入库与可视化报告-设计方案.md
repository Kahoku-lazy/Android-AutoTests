# AI Agent 运行轨迹入库与可视化报告 · 设计方案

| 项 | 内容 |
| --- | --- |
| 版本 | v1.2（定稿） |
| 状态 | 待评审 → 可立项 |
| 涉及模块 | `engines/agents`、`apps/ai_assistant`、`apps/dashboard`、`frontend` |
| 目标 | 把 Agent 运行全过程按事件类型落库，前端据此渲染可视化流程报告 |
| 本期范围 | **只做后端 + 数据库**（P1）；前端与读接口后续 |
| 变更记录 | v1.1：`ai_usage_hourly` 增 `agent_id` 并纳入唯一键<br>v1.2：不存原图；保留期统一 90 天；不做报告快照表；范围收敛为后端 |

---

## 1. 目标与非目标

### 1.1 目标

1. **完整记录轨迹**：发言 → 模型调用 → 内容块 → 工具调用 → 工具返回，一个事件一条记录
2. **按事件类型分类**：`event_type` 存框架事件类名（`ReplyStartEvent` 等），后端再派生 `phase` / `block_type`，前端不做事件名判断
3. **角色可辨**：每条记录带 `role_name`（Agent 实例名）与 `role_kind`（类型）
4. **图片可看**：截图以 base64 入库，前端拼 `data:` URI 直接渲染
5. **成本可算**：每次模型调用的 token（输入/命中/输出）与费用（输入/缓存/输出）落库并冻结
6. **时段可查**：时间精确到秒，冗余 `day` / `hour` / `is_peak`，另有小时聚合表

### 1.2 非目标

- 不做逐帧录像回放（delta 全量落行方案已否决）
- 不改现有文件日志（`logs/agents/agent_events.log` 继续保留，双写）
- 不改 AgentScope 框架内部
- 不做实时推送改造（执行中的实时视图沿用现有通道，本方案只解决落库与历史报告）

---

## 2. 总体架构与数据流

```
AgentScope 事件流
   │
   ├─ 语义行 ─────────────► 批量缓冲（50 条 / 200ms）──► ai_task_events
   │                         ↑ 任务结束/异常 finally 强制 flush
   │
   ├─ 图片 base64 片段 ────► 内存拼接 ─► 后台队列（缩略图 + sha256 去重）──► ai_task_media
   │
   ├─ ModelCallEndEvent ───┬─► ai_task_events（明细费用，8 位小数冻结）
   │                       └─► ai_usage_hourly（按 day/hour/智能体/模型/角色 upsert）
   │
   ├─ 任务结束 ────────────► 明细 SUM 回写 ai_tasks 费用列
   │
   └─ 文本 ────────────────► write_line（现有日志，不变）

上下文（task_id / case_title / step_seq / attempt / role）用 contextvars 注入
```

**边界约束**：`engines` 不 import `apps`（项目引擎边界）。所以引擎只产出结构化事件，**写库实现由平台侧注入**（见 §8）。

---

## 3. 事件分类与落行策略（20 类）

`event_type` 存图里的类名；`phase` / `block_type` 由后端映射表填好。

| # | `event_type` | `phase` | `block_type` | 落行 | 行内容 / payload |
| --- | --- | --- | --- | --- | --- |
| 1 | `ReplyStartEvent` | 开始 | reply | 1 | `{role, model}`，`started_at` |
| 2 | `ModelCallStartEvent` | 推理 | model_call | 0（记 buf） | 模型名入 buf，供 End 使用 |
| 3 | `TextBlockStartEvent` | 推理 | text | 0 | — |
| 4 | `TextBlockDeltaEvent` | 推理 | text | **0（聚合）** | 片段进 buf |
| 5 | `TextBlockEndEvent` | 推理 | text | 1 | `{text, delta_count, chars}`，起止时间 |
| 6 | `ThinkingBlockStartEvent` | 推理 | thinking | 0 | — |
| 7 | `ThinkingBlockDeltaEvent` | 推理 | thinking | **0（聚合）** | 片段进 buf |
| 8 | `ThinkingBlockEndEvent` | 推理 | thinking | 1 | `{text, delta_count}` |
| 9 | `DataBlockStartEvent` | 推理 | data | 0 | — |
| 10 | `DataBlockDeltaEvent` | 推理 | data | **0（聚合）** | base64 片段进 buf |
| 11 | `DataBlockEndEvent` | 推理 | data | 1 | `{media_type, bytes, media_id}` |
| 12 | `ToolCallStartEvent` | 推理 | tool_call | 0 | `tool_call_name` 入 buf |
| 13 | `ToolCallDeltaEvent` | 推理 | tool_call | **1 行/条** | `{delta, idx}` |
| 14 | `ToolCallEndEvent` | 推理 | tool_call | 1 | `{tool_name(来自 buf), args}`，起止时间 |
| 15 | `ModelCallEndEvent` | 推理 | model_call | 1 | `{model(来自 buf), finished_reason}` + token / cost 列 |
| 16 | `ToolResultStartEvent` | 执行 | tool_result | 0 | `tool_call_name` 入 buf |
| 17 | `ToolResultTextDeltaEvent` | 执行 | tool_result | **1 行/条** | `{delta, idx}` |
| 18 | `ToolResultDataDeltaEvent` | 执行 | tool_result | **0（聚合）** | base64 片段进 buf |
| 19 | `ToolResultEndEvent` | 执行 | tool_result | 1 | `{tool_name, status(state), result, media_id}`，耗时 |
| 20 | `ReplyEndEvent` | 结束 | reply | 1 | `{finished_reason}`，本轮耗时 |

### 3.1 策略说明（B+）

- **聚合类**：`TextBlockDelta` / `ThinkingBlockDelta` / `DataBlockDelta` —— 占行数 95% 以上，内容由 End 事件等价覆盖
- **逐条落行**：`ToolCallDelta` / `ToolResultTextDelta` —— 一个块只有 5~30 条，成本可忽略，保留"参数分几次到达"的细节
- **Start 类不落行，信息不丢**：End 行带 `started_at` / `ended_at`，块的时间跨度仍可绘制

### 3.2 框架事实（已核实 `agentscope/event/_event.py`）

1. `ModelCallStartEvent` 有 `model_name`，`ModelCallEndEvent` **没有** → 模型名必须从 Start 事件带入
2. `ToolCallEndEvent` 只有 `reply_id` + `tool_call_id`，**无工具名、无入参** → 名字来自 Start，入参由 delta 拼接
3. `ToolResultEndEvent` 只有 `state` → 工具名来自 `ToolResultStartEvent.tool_call_name`，结果文本由 text delta 拼接
4. `ReplyStartEvent.name` 是**角色名**（`executor_role` / `verifier_role`），其余事件不带 → 需在 reply 内继承

### 3.3 行数估算

| 项 | 单任务 |
| --- | --- |
| 语义行（B+） | **200~500** |
| 若 delta 全量落行（已否决） | 3 000~7 000 |

---

## 4. 数据模型

> 类型以 MySQL 表述；SQLite 由 Django 自动映射（`JSON` → `TEXT`，`DECIMAL` → `NUMERIC`）。

### 4.1 `ai_task_events` —— 事件主表（小而密）

```sql
CREATE TABLE ai_task_events (
  id                    BIGINT PRIMARY KEY AUTO_INCREMENT,
  task_id               BIGINT NOT NULL,
  case_title            VARCHAR(255) NOT NULL DEFAULT '',
  step_seq              INT NULL,              -- 平台层注入
  attempt               INT NULL,              -- 第几次尝试
  seq                   INT NOT NULL,          -- 任务内单调，排序与配对靠它
  reply_id              VARCHAR(64) NOT NULL DEFAULT '',
  block_id              VARCHAR(64) NOT NULL DEFAULT '',
  tool_call_id          VARCHAR(64) NOT NULL DEFAULT '',

  event_type            VARCHAR(48) NOT NULL,  -- 框架类名
  phase                 VARCHAR(8)  NOT NULL,  -- 开始/推理/执行/结束
  block_type            VARCHAR(16) NOT NULL,  -- reply/model_call/text/thinking/data/tool_call/tool_result
  is_delta              TINYINT(1)  NOT NULL DEFAULT 0,

  role_name             VARCHAR(64) NOT NULL DEFAULT '',  -- Agent 实例名：executor_role
  role_kind             VARCHAR(16) NOT NULL DEFAULT '',  -- 统计类型：executor/verifier/planner
  model                 VARCHAR(64) NOT NULL DEFAULT '',
  status                VARCHAR(16) NOT NULL DEFAULT '',
  payload               JSON NULL,

  started_at            DATETIME NULL,         -- 北京时间，秒精度
  ended_at              DATETIME NULL,
  duration_ms           INT NOT NULL DEFAULT 0,

  -- 仅 ModelCallEndEvent 有值
  called_at             DATETIME NULL,
  called_date           DATE NULL,
  called_hour           TINYINT NULL,
  is_peak               TINYINT(1) NULL,
  input_tokens          INT NOT NULL DEFAULT 0,
  cache_input_tokens    INT NOT NULL DEFAULT 0,
  cache_miss_tokens     INT NOT NULL DEFAULT 0,
  output_tokens         INT NOT NULL DEFAULT 0,
  cache_creation_tokens INT NOT NULL DEFAULT 0, -- 诊断用，不计费
  cost_input            DECIMAL(14,8) NOT NULL DEFAULT 0,
  cost_cache            DECIMAL(14,8) NOT NULL DEFAULT 0,
  cost_output           DECIMAL(14,8) NOT NULL DEFAULT 0,
  cost_total            DECIMAL(14,8) NOT NULL DEFAULT 0,
  pricing_snapshot      JSON NULL,

  media_id              BIGINT NULL,
  created_at            DATETIME NOT NULL
);
CREATE INDEX idx_evt_task_seq  ON ai_task_events (task_id, seq);
CREATE INDEX idx_evt_task_type ON ai_task_events (task_id, event_type);
CREATE INDEX idx_evt_usage     ON ai_task_events (called_date, called_hour);
```

### 4.2 `ai_task_media` —— 图片（大而稀）

```sql
CREATE TABLE ai_task_media (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  task_id      BIGINT NOT NULL,
  event_seq    INT NULL,               -- 哪条 tool_result 带来的
  role_name    VARCHAR(64) NOT NULL DEFAULT '',
  step_seq     INT NULL,
  attempt      INT NULL,
  sha256       CHAR(64) NOT NULL,
  media_type   VARCHAR(32) NOT NULL,
  bytes        INT NOT NULL,           -- 原图字节数
  width        INT NULL,
  height       INT NULL,
  thumb_b64    LONGTEXT NULL,          -- 缩略图 base64（长边 720 JPEG）；不存原图
  created_at   DATETIME NOT NULL,
  UNIQUE KEY uk_media_task_sha (task_id, sha256)
);
CREATE INDEX idx_media_task_step ON ai_task_media (task_id, step_seq);
```

### 4.3 `ai_usage_hourly` —— 时段消费

```sql
CREATE TABLE ai_usage_hourly (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  stat_date    DATE NOT NULL,          -- 北京时间
  stat_hour    TINYINT NOT NULL,       -- 0~23
  is_peak      TINYINT(1) NOT NULL,    -- 由（日期, 小时）唯一决定
  agent_id     BIGINT NOT NULL DEFAULT 0,  -- 哪个智能体（软引用，见下）
  model        VARCHAR(64) NOT NULL,
  role_name    VARCHAR(64) NOT NULL,
  role_kind    VARCHAR(16) NOT NULL,
  calls        INT NOT NULL DEFAULT 0,

  input_tokens         BIGINT NOT NULL DEFAULT 0,
  cache_input_tokens   BIGINT NOT NULL DEFAULT 0,
  cache_miss_tokens    BIGINT NOT NULL DEFAULT 0,
  output_tokens        BIGINT NOT NULL DEFAULT 0,

  cost_input   DECIMAL(12,4) NOT NULL DEFAULT 0,
  cost_cache   DECIMAL(12,4) NOT NULL DEFAULT 0,
  cost_output  DECIMAL(12,4) NOT NULL DEFAULT 0,
  cost_total   DECIMAL(12,4) NOT NULL DEFAULT 0,
  updated_at   DATETIME NOT NULL,
  UNIQUE KEY uk_slot (stat_date, stat_hour, model, role_name, agent_id),
  KEY idx_usage_agent (agent_id, stat_date)
);
```

写入用 upsert（MySQL `ON DUPLICATE KEY UPDATE`）。一天最多 24 × 智能体数 × 模型数 × 角色数，量级仍是几十到几百行。

**为什么 `agent_id` 用软引用（`BIGINT NOT NULL DEFAULT 0`，不加外键）**：

- `AIAgent` 删除会级联删除其 `AITask`，但**历史消费统计不应随智能体一起消失**
- 若用 `SET_NULL`，唯一键里的 `agent_id` 变 `NULL` 后 MySQL 视 NULL 互不相等，upsert 会产生重复行
- 因此存裸 id，`0` 表示未知/已删除；需要展示名字时按 id 查 `ai_agents`，查不到显示「已删除」

`ai_task_events` / `ai_task_media` **不加** `agent_id`：它们能从 `task_id → ai_tasks.agent_id` 关联，避免冗余列漂移。

### 4.4 `ai_tasks` 增列

```sql
ALTER TABLE ai_tasks
  ADD cost_input  DECIMAL(12,4) NOT NULL DEFAULT 0,
  ADD cost_cache  DECIMAL(12,4) NOT NULL DEFAULT 0,
  ADD cost_output DECIMAL(12,4) NOT NULL DEFAULT 0,
  ADD cost_total  DECIMAL(12,4) NOT NULL DEFAULT 0;
```

任务结束时由明细 SUM 回写；Dashboard 改读这四列。

---

## 5. 图片存储

| 项 | 数值 |
| --- | --- |
| 原图（**不存**） | 566 827 B PNG → base64 755 772 字符（真机实测） |
| 缩略图（长边 720 JPEG q80） | ~60 KB → base64 **~80 KB** |
| 单任务（去重后 ~12 张，仅缩略图） | **~1 MB** |

规则：

1. **只存 `thumb_b64`，不存原图**（原图 base64 755 KB/张，体积不值得）
2. 同任务内 `sha256` 去重（executor 连续截图常完全相同，可省 30~50%）
3. 单任务图片上限 **40 张**，超出记 `truncated: true`
4. base64 在内存拼接后**异步入库**，不阻塞事件流
5. 前端拼 `data:image/jpeg;base64,{thumb_b64}` 直接渲染

---

## 6. token 与费用

### 6.1 token 口径（代码事实 `billing.py:75-81`）

```python
hit  = min(cache_hit_tokens, input_tokens)
miss = input_tokens - hit
```

即 **`input_tokens` 已包含命中部分**。

| 列 | 含义 |
| --- | --- |
| `input_tokens` | 总输入（含命中） |
| `cache_input_tokens` | 其中命中缓存 |
| `cache_miss_tokens` | 未命中（派生，冗余存储省计算） |
| `output_tokens` | 输出 |
| `cache_creation_tokens` | 诊断值，DeepSeek 无此计费项 |

### 6.2 费用三项

| 列 | 计算 |
| --- | --- |
| `cost_input` | `cache_miss_tokens × 未命中单价 × multiplier` |
| `cost_cache` | `cache_input_tokens × 命中单价 × multiplier` |
| `cost_output` | `output_tokens × 输出单价 × multiplier` |
| `cost_total` | 三者之和 |

### 6.3 三条硬规则

**① 明细 8 位小数，聚合 4 位**

`DeepSeekBilling.cost()` 内部已 `_four_decimal_places()`（4 位）。flash 命中价 0.02 元/百万：

```
1000 token 命中 = 0.00002 元 → 4 位小数 = 0.0000（被抹平）
```

明细层必须用**未量化 Decimal** 计算；聚合层再量化。

**② 费用冻结**

单价是硬编码常量、是否高峰依赖调用时刻与节假日库，重算历史必然漂移 → `pricing_snapshot` 必须落库：

```json
{"model": "deepseek-flash", "hit_price": 0.02, "miss_price": 1, "output_price": 4,
 "multiplier": 2, "peak": true}
```

**③ 全链路北京时间**

高峰 = 北京时间工作日 9:00–12:00、14:00–18:00，法定节假日不算。`called_date` / `called_hour` / `is_peak` 一律按 `Asia/Shanghai` 切分。每小时完整落在同一档内（9/10/11 高峰，12/13 空闲，14~17 高峰），因此 `(日期, 小时)` 唯一决定 `is_peak`。

### 6.4 与现有任务级计费的差异

`apps/ai_assistant/deepseek_billing.py::task_deepseek_cost` 现用 **`finished_at` 一个时刻**判高峰并实时重算。本方案按**每次调用时刻**分别判定：

> **跨 12:00 / 14:00 / 18:00 边界的任务，两种算法结果不同。**

定稿口径：**以明细 SUM 为准**；旧函数只保留给无明细的历史任务兜底。

### 6.5 常用查询

```sql
-- 某天各时段
SELECT stat_hour, is_peak, SUM(input_tokens), SUM(cache_input_tokens),
       SUM(output_tokens), SUM(cost_total)
FROM ai_usage_hourly WHERE stat_date = '2026-10-20'
GROUP BY stat_hour, is_peak ORDER BY stat_hour;

-- 高峰 vs 空闲占比
SELECT is_peak, SUM(cost_total) FROM ai_usage_hourly GROUP BY is_peak;

-- 按角色
SELECT role_kind, SUM(cost_total) FROM ai_usage_hourly GROUP BY role_kind;

-- 按智能体（哪个最费）
SELECT agent_id, SUM(cost_total) AS cost, SUM(input_tokens + output_tokens) AS tokens
FROM ai_usage_hourly GROUP BY agent_id ORDER BY cost DESC;
```

---

## 7. 写入管线

| 环节 | 做法 |
| --- | --- |
| 上下文注入 | `contextvars`：任务级 `task_id` / `agent_id` / `case_title`；步骤级 `step_seq` / `attempt`；发言级 `role_name` / `role_kind` |
| 批量写入 | 语义行进内存队列，50 条或 200ms flush |
| 收尾 | `finally` 强制 flush（取消/异常不能丢尾巴） |
| 图片 | base64 拼接 → 后台任务（缩略图编码 + sha256 去重 + 入库） |
| 小时聚合 | 每次 `ModelCallEndEvent` upsert `ai_usage_hourly` |
| 任务汇总 | 结束：`SUM(明细)` → 回写 `ai_tasks` 费用列 |
| 日志 | `write_line` 保持不变，双写 |

**禁止**：在 `show()` 里同步写 DB；delta 事件触发 DB 写。

---

## 8. 模块归属与本方案的文件落点

### 8.1 归属结论

**全部新增表、模型、写库、读接口都放 `apps/ai_assistant`。**

理由：
- `AITask` 在 `ai_assistant`，事件/媒体/用量都是**任务的从属数据**，同库同 App 便于级联删除与事务
- 平台侧唯一写入入口是 `apps/ai_assistant/task_runner.py`（它调用 `run_platform_sop`）
- `apps/dashboard` 只做统计展示，**只读**，跨 App 读 Model 是项目允许的
- `apps/report_generator` 只管报告导出，不存过程数据（P4 时从 ai_assistant 读）

### 8.2 边界：引擎只产事件，不碰 DB

`engines` MUST NOT import `apps`。因此：

```
engines/agents/event_sink.py        新增：EventSink 协议 + 默认空实现 + bind_sink()
engines/agents/messaging/messages.py 改造：产出结构化事件 → 交给 sink
apps/ai_assistant/event_store.py    新增：实现 sink（批量写库、缩略图、用量 upsert）
apps/ai_assistant/task_runner.py    改造：任务启动前 bind_sink(DjangoEventSink(task_id, agent_id))
```

### 8.3 文件清单

| 层 | 文件 | 改动 |
| --- | --- | --- |
| 引擎 | `engines/agents/event_sink.py` | 新增：协议、contextvar、默认空 sink |
| 引擎 | `engines/agents/messaging/messages.py` | 改造：结构化输出 + B+ 聚合 + 图片拼接 + 角色继承 |
| 引擎 | `engines/agents/messaging/billing.py` | 新增：未量化的费用计算入口 |
| 引擎 | `engines/agents/workflow/platform_run.py` | 小改：把 `task_id` 传给 workflow |
| 引擎 | `engines/agents/workflow/ui_auto_workflow.py` | 小改：按步注入 `step_seq` / `attempt`；结束 flush |
| 后端 | `apps/ai_assistant/models.py` | 新增 3 个模型 + `AITask` 4 列 |
| 后端 | `apps/ai_assistant/migrations/0058_*.py` | 新增迁移 |
| 后端 | `apps/ai_assistant/event_store.py` | 新增：sink 实现、缩略图、去重、用量 upsert |
| 后端 | `apps/ai_assistant/api.py` | 新增：事件/媒体/用量读写入口、任务费用回写 |
| 后端 | `apps/ai_assistant/views_drf.py` | 新增 4~5 个只读端点 |
| 后端 | `apps/ai_assistant/urls.py` | 新增路由 |
| 后端 | `apps/ai_assistant/serializers.py` | 新增事件/媒体序列化 |
| 后端 | `apps/ai_assistant/task_runner.py` | 小改：绑定 sink（带 `task_id` / `agent_id`） |
| 后端 | `apps/dashboard/ai_usage.py` | 改造：改读 `ai_tasks.cost_*` 与 `ai_usage_hourly` |
| 前端 | `frontend/src/modules/ai-assistant/` | 新增：泳道图、报告页、指标卡、api 层 |
| 测试 | `tests/engines/agents/` | 新增：事件映射、B+ 聚合、费用精度、去重 |

---

## 9. 接口契约

| 方法 | 路径 | 返回 | 备注 |
| --- | --- | --- | --- |
| GET | `/api/ai/tasks/{id}/timeline?after_seq=&limit=100&event_types=&include_delta=false` | 事件列表 | **不含 payload、不含 base64** |
| GET | `/api/ai/tasks/{id}/events/{seq}` | 单条事件（含 payload） | 点开才取 |
| GET | `/api/ai/tasks/{id}/media/{media_id}` | `{media_type, base64}` | 只返回缩略图 base64 |
| GET | `/api/ai/usage/hourly?from=&to=&model=&role_kind=` | 时段消费序列 | 图表数据源 |
| GET | `/api/ai/usage/daily?from=&to=` | 按天汇总 | — |

响应信封 `{status, data}`，JSON snake_case。

---

## 10. 前端渲染契约

后端返回每条事件都带 `phase` + `block_type` + `role_name`，前端**不做事件名判断**：

| `phase` | 视觉 |
| --- | --- |
| 开始 | 泳道起点卡片（`role_name` + 模型） |
| 推理 | 模型调用分组：思考/文本块默认折叠，工具调用块展开 |
| 执行 | 工具返回块：状态色 + 结果摘要 + 图片缩略图条 |
| 结束 | 终点卡片（完成原因 + 耗时） |

- 泳道时序：按 `role_name` 分泳道（executor / verifier 各一条），按 `seq` 铺开
- 步骤 DAG（P3）：数据来自 `engine.state.steps`，不是事件表
- 指标卡：任务总 token（三项）+ 总费用（三项 + 合计）+ 缓存命中率 + 耗时
- 图表：ECharts 按小时消费柱状图，高峰段不同色

---

## 11. 容量、清理与性能

| 项 | 估算 |
| --- | --- |
| 单任务事件 | 200~500 行（~0.25 MB） |
| 单任务媒体（缩略图） | ~1 MB |
| 每天 50 任务 | 事件 ~2.5 万行、媒体 ~50 MB |
| 保留 90 天（事件 + 媒体） | 事件 ~1.1 GB、媒体 **~4.5 GB** |

策略：

- 任务删除 → 事件/媒体级联删
- 事件保留 **90 天**，媒体保留 **90 天**（独立清理任务，同一套 TTL）
- `ai_usage_hourly` 永久保留（一年几千行）
- **列表接口永不 `SELECT *`**；媒体表独立，ORM 不反查

---

## 12. 改动规模评估

### 12.1 按文件

| 类型 | 文件数 | 新增/改动行数（估） | 本期 |
| --- | --- | --- | --- |
| 引擎侧 | 5 | ~450 | ✅ |
| 后端 apps | 9 | ~700 | ✅ |
| 前端 | 5~7 | ~800 | ⏸ 后续 |
| 测试 | 3~4 | ~300 | ✅（后端部分） |
| **本期合计（不含前端）** | **~17 个文件** | **~1 450 行** | |
| 全量合计 | ~22 个文件 | ~2 250 行 | |

### 12.2 按阶段

| 阶段 | 内容 | 行数（估） | 风险 |
| --- | --- | --- | --- |
| **P1（本期）** | 三张表 + 事件结构化 + sink + 批量写入 + 图片入库 + 小时聚合 | ~900 | 中（动 `messages.py` 核心） |
| **P2（后端）** | 读接口：timeline / event detail / media / usage | ~250 | 低 |
| P3（前端） | 泳道图 + 步骤 DAG + 指标卡 + 消费图表 | ~800 | 低 |
| P4 | 导出 + 清理任务 | ~200 | 低 |

### 12.3 依赖与影响面

| 影响 | 说明 |
| --- | --- |
| `apps/dashboard/ai_usage.py` | 改读冻结费用列，输出口径可能微调（跨边界任务金额变化） |
| `apps/ai_assistant/deepseek_billing.py` | 退为兜底（历史无明细任务） |
| `AgentEventsShow` | 内部结构大改，外部调用方（2 处）签名不变 |
| 数据库 | 3 张新表 + `ai_tasks` 4 列；无破坏性变更 |

---

## 13. 落地阶段

| 阶段 | 验收 |
| --- | --- |
| **P1（本期：后端 + 数据库）** | 跑一个任务：事件 200~500 行、`event_type` 分布符合 §3、媒体表有缩略图、小时表有行（含 `agent_id`）、`ai_tasks` 费用列有值 |
| P2（后端） | 4 个只读接口可用，返回结构与 §9 一致 |
| P3（前端） | 报告页能按四阶段分组渲染并展开工具明细；首屏出步骤 DAG 与总账指标 |
| P4 | 可导出 HTML/PDF；清理任务按 90 天 TTL 执行 |

---

## 14. 风险与对策

| 风险 | 对策 |
| --- | --- |
| 单次调用费用被 4 位小数抹成 0 | 明细 8 位、聚合 4 位 |
| 跨高峰边界对账不一致 | 以明细 SUM 为准，旧算法兜底 |
| 图片写库阻塞事件流 | 异步入库 + 队列 |
| `SELECT *` 拉 base64 撑爆内存 | 独立媒体表 + 投影字段 |
| 任务取消丢失尾部事件 | `finally` 强制 flush |
| 框架升级改事件类名 | 关键逻辑不依赖类名（用 `phase` / `block_type`），类名只作展示分类 |
| 时区错乱 | 全链路固定 `Asia/Shanghai` |
| 引擎 import apps 破坏边界 | 通过 sink 注入，引擎零 apps 依赖 |

---

## 15. 决策记录

### 已定（v1.2）

| 项 | 结论 |
| --- | --- |
| `ai_usage_hourly` 是否带 `agent_id` | **带**，并纳入唯一键 `(stat_date, stat_hour, model, role_name, agent_id)`；裸 id 软引用，不加外键 |
| 事件/媒体表是否带 `agent_id` | 不带，经 `task_id → ai_tasks.agent_id` 关联 |
| 是否存原图（`full_b64`） | **不存**，只存缩略图 base64 |
| 保留期 | 事件 **90 天**、媒体 **90 天**（同一套 TTL） |
| `ai_task_reports` 快照表 | **本期不做** |
| 本期范围 | 只做后端 + 数据库；前端与读接口按 P2/P3 排后 |

### 待定

无。方案已闭环，可进入 OpenSpec 立项。
