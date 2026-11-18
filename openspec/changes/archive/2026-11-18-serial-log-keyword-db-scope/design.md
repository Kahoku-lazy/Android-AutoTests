## Context

动机见 proposal.md - Why。方案所需的现状约束：

- 关键词真相源是 `backend/config/device_log_keywords.json`（67 关键词 / 56 功能点，一个关键词可挂多个功能点，功能点带全局编号 #0~#55）；读取统一经 `engines/device/logbus.py` 的 `KeywordIndex.from_file()`。
- `KeywordIndex(mapping)` 构造器已支持直接注入 dict——这是「DB 真相源 + engines 零 Django」的关键注入口。
- `serial_log` App 已有表 `sl_log_ports` 与纪律「唯一写点 `api.py`、View 只分发、跨 App 读 Model / 写走对方 api」；数据迁移 precedent 是 `0002_copy_port_state`（用 `apps.get_model` 读历史模型）。
- 现行规格 `device-log-keyword-catalog` 钉死「恰三列、只读、来源 file、重启生效文案」；前端模块 AGENTS 红线「改表仍走文件」。两者都需经本变更的 delta 与变更申请修改。
- 平台 DB 支持 sqlite / mysql 双引擎（`DB_ENGINE`），迁移必须两者通用。
- **并行变更协调**：`add-serial-log-custom-ports`（2026-11-18 获批，实施中）已把端口双轨制 `origin` 字段落进 `models.py`，其迁移预计占用 `serial_log` 的 0003。该单修改的是端口相关三条需求，与本单的关键词需求**无需求级重叠**；但共享 `models.py` / `api.py` / 迁移目录，本单迁移编号必须在其落地后顺延（见 D4 与 Risks）。
- 遗留资产（本单不处理，见 Non-Goals）：`task_list/log_history.keyword_catalog_text()` 与 `ae_harness/agents/config.load_log_keywords(sku)` 当前均无生产调用方；`tests/serial_log/unit/test_log_keyword_catalog.py` 指向已删除的 `engines/agents` 路径，属失效测试。

## Goals / Non-Goals

**Goals:**

- 关键词表落库 `sl_log_keywords`，范围（通用 / SKU 专用）成为一等字段，并集口径可被跨模块复用。
- 存量条目无损迁入（编号、名称、行序、一对多关系全保留），迁移确定、可回滚、双引擎通用。
- 目录接口与页面如实呈现数据库来源与范围列，页面保持只读。

**Non-Goals:**

- 不做 HTTP 写接口与编辑 UI（二期另立变更）。
- 不复活 `check_device_log` / 证据窗口等已退役链路；不改 `KeywordIndex.match()`。
- 不退役按 SKU md 目录（`H6810.md`）与 `keyword_catalog_text()` / `load_log_keywords()`——它们当前无生产调用方，去留随二期验收链路方案决定。
- 不动 `sl_log_ports`、端口监听与采集写文件链路。

## Decisions

**D1 扁平单表，一行 = 关键词 × 功能点 × 范围。**
备选：① 关键词 / 功能点 / 映射三表规范化——同功能点挂多关键词时一致性更好维护，但当前 ~70 行规模 join 复杂度无收益；② JSON 保留真相源、DB 做镜像——双真相源必然漂移，违背需求意图。取扁平单表：与现有 JSON、前端行结构同构，迁移无损。

表结构（`serial_log/models.py` 新增 `LogKeyword`）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BigAutoField | 主键 |
| `keyword` | CharField(200) | 关键词原文 |
| `feature_id` | IntegerField | 功能点业务编号（沿用 #0~#55，新增续编） |
| `module` | CharField(100) | 功能模块名 |
| `feature` | CharField(200) | 功能点名 |
| `scope` | CharField(100)，默认 `"*"` | `"*"`=通用；否则 SKU 名 |
| `sort_order` | IntegerField，默认 0 | 表内行序 |
| `created_at` / `updated_at` | DateTimeField | auto_now_add / auto_now |

Meta：`db_table="sl_log_keywords"`，`ordering=["sort_order","id"]`，`UniqueConstraint(fields=["keyword","feature_id","scope"], name="uniq_sl_kw_keyword_feature_scope")`，`scope` 单列索引。

**D2 scope 存机器值 `"*"` / SKU 名，不存中文展示值。**
与 `LogSourceSpec.sku` / `DEFAULT_CHANNEL="*"` 约定对齐，按 SKU 取词时直接字符串相等匹配，无需翻译层。展示映射（`*`→「通用」、`H6601`→「H6601专用」）放前端 constants。备选「存字面量『通用』/『H6601专用』」被否：匹配与筛选都要解析中文后缀，脆弱。api 层校验 scope 取值：`"*"` 或满足 `^[A-Za-z0-9_-]+$` 的 SKU 名（与 ae_harness 的 SKU 白名单同形）。

**D3 保留 feature_id 业务编号，不用主键当编号。**
同一功能点可挂在多个关键词下（如 #2 与 #17 同挂 `color_configs_set_success`），编号是跨行稳定的业务标识，页面与既有引用都按它展示。新增条目由 api 取 `max(feature_id)+1` 续编；编号允许空洞，不做重排。

**D4 迁移冻结快照，不在 migrate 时读文件。**
建表迁移 + 数据迁移（编号**暂定** 0003/0004；因 `add-serial-log-custom-ports` 的 `origin` 迁移预计占用 0003，实施时以 `serial_log` 当时最新迁移为依赖顺延，以 `makemigrations` 实际生成为准）。数据迁移把当前 JSON 内容以 Python 字面量冻结进迁移（~70 行），`scope="*"`，`sort_order` 按原表顺序以 10 为步长赋值（10, 20, 30…留插入空隙），用 `apps.get_model` + `get_or_create` 幂等写入（沿用 `0002_copy_port_state` precedent）。备选「migrate 时读 JSON」被否：部署时文件可能缺失或已被手改，结果不确定。reverse：数据迁移清空本表行、建表迁移删表；JSON 文件保留不动，旧代码回退后仍可按文件读。

**D5 读路径：api 出数据，keywords.py 只组装。**
`api.py` 新增只读函数：`list_keyword_rows()`（全量按 sort_order）、`keyword_mapping_for_sku(sku)`（并集：`scope="*"` ∪ `scope=sku`，返回 `dict[keyword, list[{id,module,feature}]]`，可直接注入 `KeywordIndex(mapping)`）。`keywords.collect_keywords()` 改调 api，`origin="db"`，`updated_at` 取表内 `max(updated_at)`（北京时间秒精度，沿用现有格式）。空表给可读 note，不抛错。

**D6 契约最小改动：保持分组形状，功能点条目加 scope。**
`keywords: [{keyword, features:[{id, module, feature, scope}]}]` 不变外层；**移除 `keyword_file` 字段**（文件已退役，前端 `api.ts` 类型同步移除），`origin` 取值改为 `"db" | "none"`。备选「扁平 rows 数组」被否：契约 diff 更大，分组形状与计数口径现成。计数口径不变：关键词按原文去重、功能点按「模块+编号+名称」去重，范围不参与去重（同一词跨范围仍计 1 个关键词）。

**D7 一期写路径只到 api 层，不暴露 HTTP。**
`api.py` 提供维护函数 `upsert_keyword(keyword, feature_id, module, feature, scope, sort_order)` 与 `delete_keyword(row_id)`（upsert 按唯一键 update_or_create；scope 校验见 D2），供迁移核对、管理命令或 shell 维护使用；View 层不新增写端点。运行时一切写入收敛于此，与 `sl_log_ports` 同纪律。迁移内的批量写入走 `apps.get_model`（D4），属迁移特权，不算运行时绕过。

**D8 前端：第四列 + 范围筛选，纯函数先行。**
`helpers/log-keyword-rows.ts`：行结构加 `scope`，row-key 纳入 scope；新增 `filterKeywordRowsByScope(rows, scope)` 纯函数；计数函数口径不变。`constants.ts`：新增范围列标题、范围渲染映射（`*`→通用）、筛选选项文案；**移除 `LOG_KEYWORD_RESTART_HINT` 重启文案**，origin 标签加 `db`。`LogKeywordPanel.vue`：COLUMNS 加第四列（范围）、搜索条旁加 `.sketch-kit` 范围下拉（全部/通用/各 SKU，选项从全量行动态派生）；模块配色仍按全量行首次出现顺序分配，筛选不漂移。样式只改本组件私有 `sl-*` / `lk-*` 类与令牌。

**D9 engines 零改动。**
`KeywordIndex.from_file` 与 `DEVICE_LOG_KEYWORD_FILE` 配置保留（控制台兜底与回退路径）；平台侧取词一律 D5 的 api → mapping 注入。不新增 engines 对 backend 的任何依赖。

## 模块防火墙自检

- **跨 App import**：本变更不新增跨 App 依赖。`serial_log` 只被读（Model / api）；`task_list/log_history.py` 现状直读文件且无调用方，本单不动它（二期若复活验收注入，改经 `serial_log.api.keyword_mapping_for_sku`，届时不 import 对方内部实现）。
- **写入收敛**：`sl_log_keywords` 全部运行时 INSERT/UPDATE/DELETE 收敛在 `serial_log/api.py`；View 只分发；迁移用 `apps.get_model` 属历史模型特权（precedent 0002）。
- **前端不直连数据库**：前端只经 `GET /api/serial-log/keywords/`；一期无写请求。仪表盘不涉及。
- **engines 边界**：零 `django.*` / `apps.*` import 新增；`KeywordIndex` 只收注入的 dict。
- **依赖方向**：backend → engines 注入不变，无反向依赖。

## 红线变更申请（硬约束：经需求方确认后才动 AGENTS 文件）

**改什么：**
1. `frontend/src/modules/serial-log/AGENTS.md` 红线段「关键词表**只读**：不提供新增 / 编辑 / 删除 / 上传 / 保存入口，改表仍走 `DEVICE_LOG_KEYWORD_FILE` 指向的文件」→ 改为「关键词表**只读**：不提供新增 / 编辑 / 删除 / 上传 / 保存入口；关键词真相源为数据库 `sl_log_keywords`，改表经后端 `serial_log/api.py`（一期无页面写入口）」。只读红线本身不放开。
2. `backend/apps/serial_log/AGENTS.md` 职责段登记新表 `sl_log_keywords`（关键词对照表持久化），「写库与边界」段把唯一写点条款扩展为「`sl_log_ports` 与 `sl_log_keywords` 的唯一写点是 `api.py`」；接口表不变（一期无新端点）。该文件现行版本已含端口双轨制条款（2026-11-18 获批），本申请**只追加关键词表条款**，不动双轨制与自定义端口条款。

**为什么必须改：** 真相源由文件变为数据库是本变更的核心行为；原条款「改表仍走文件」与新规约直接矛盾，不改则文档与实现背离，后续 AI 会按旧红线拒绝合法改动或走错写路径。

**影响面：** 仅这两份 AGENTS 的上述条款；规格 delta（`serial-log-module`、`device-log-keyword-catalog`）随本变更归档同步；不影响其它模块红线与依赖边界。

**怎么回退：** 两处条款均为文本替换，回退即恢复原文；代码回退走迁移 reverse（D4），文件真相源仍在，旧条款重新成立。

## Risks / Trade-offs

- [迁移后有人仍手改 JSON，造成「改了没生效」] → JSON 头部 description 标注「已迁库，勿再手改」；平台展示与取词不再读文件；一致性测试以 DB 为准。
- [快照与迁移时点的真实文件不一致（落单到实施之间文件被改）] → 实施第一步重新核对 JSON 现状，若有变动以实施时点内容重新冻结快照并在 tasks 记录差异。
- [feature_id 续编冲突（并发维护）] → 一期无 HTTP 写口，维护经单点 api；唯一约束兜底防重复行；编号是业务标签，允许空洞。
- [双引擎迁移差异（sqlite / mysql）] → 只用标准 ORM 与 RunPython，无裸 SQL；关单前两种引擎各做一次全新安装 + 升级演练。
- [范围筛选引入后计数/配色口径漂移] → 计数恒报全量、配色按全量行分配，均写成规格场景并配前端纯函数单测。
- [一期改词只能走维护函数，运营不便] → 显式取舍：二期补超管编辑 UI；一期在来源说明里如实标注「条目来自数据库」。
- [失效测试 `test_log_keyword_catalog.py` 在实施前继续报错] → 本单任务内重写为「DB 条目与冻结快照一致」校验，不再引用已删除路径。
- [与 `add-serial-log-custom-ports` 并行实施：迁移编号冲突、同文件改动互相覆盖] → 实施前先核对该单落地状态，本单迁移依赖其最新编号顺延；两单需求面不重叠（其改端口三需求，本单改关键词需求）；`models.py` / `api.py` 改动按功能分区追加，合入前逐行 review diff，禁止整文件覆盖。

## Migration Plan

1. 合入代码（模型 + 迁移 + api + 读路径 + 前端），AGENTS 条款变更须先获需求方确认；确认 `add-serial-log-custom-ports` 的迁移已落地，本单迁移编号在其之后顺延。
2. `python manage.py migrate serial_log`：建表迁移 → 冻结快照数据迁移。
3. 核对：关键词数 = 67、功能点数 = 56（以实施时点 JSON 为准）、行序与原表一致、scope 全为 `*`。
4. 前端构建刷新后验证四列与范围筛选；来源说明显示数据库与最近写入时间。
5. **回滚**：`python manage.py migrate serial_log <本单建表迁移的前一编号>`（reverse 清行删表，保留其前的端口迁移）→ 回退代码；JSON 文件未动，旧版按文件读取照常。

## Open Questions

（无阻塞性未决项；按 SKU md 目录与旧验收注入函数的退役时机属二期范围，见 Non-Goals。）
