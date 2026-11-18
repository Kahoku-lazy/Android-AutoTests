## Why

日志关键词对照表目前是手工维护的 JSON 文件（`backend/config/device_log_keywords.json`），改表要编辑文件并重启平台，且没有「范围」维度——所有关键词对全部型号共用。随着被测型号增多（H6601、H2234 等），型号专用关键词无处登记；现有的按 SKU md 目录（`engines/ae_harness/agents/config/log_keywords/`）与全量 JSON 双份手工维护，已经出现漂移与失效测试。需要把关键词表迁入数据库，使变动可持久化、可审计，并支持「通用 / SKU 专用」范围。

## What Changes

- 新增表 `sl_log_keywords`（`serial_log` App 独占，沿用 `sl_` 前缀）：一行 = 一个「关键词 × 功能点 × 范围」。字段：`keyword` / `feature_id` / `module` / `feature` / `scope` / `sort_order` / `created_at` / `updated_at`；唯一约束 `(keyword, feature_id, scope)`。
- 范围语义：`scope="*"` 表示**通用**（与引擎层 `DEFAULT_CHANNEL="*"` 约定对齐），其余存 SKU 名（如 `H6601`，页面渲染「H6601专用」）。**并集口径**：通用永远生效，SKU 专用是增量；某 SKU 可用关键词 = 通用 ∪ 该 SKU 专用。
- 数据迁移把当前 JSON 内容**冻结为快照**一次性迁入（范围全部为通用、按原顺序编 `sort_order`、保留功能点编号 #0~#55）；不在 migrate 时读文件。迁移后 JSON 退役为种子档案（保留文件并标注「已迁库，勿再手改」）。
- `GET /api/serial-log/keywords/` 改从数据库读取：功能点条目新增 `scope` 字段，取值来源标为数据库，更新时间取表内最新写入时间；空态语义不变。**页面保持只读**。
- 前端关键词表新增第四列「范围」与范围筛选（通用 / 各 SKU）；搜索、计数与模块配色口径不变。
- `serial_log/api.py` 成为关键词表**唯一写点**：一期只提供迁移导入与维护函数，**不暴露 HTTP 写接口**；跨模块按 SKU 取词经 `api.py` 的并集查询函数，后端组装 mapping 注入 `KeywordIndex(mapping)`。
- `engines/` 零改动（`KeywordIndex(mapping)` 注入口已就绪，引擎层不碰 Django）。
- 重写失效测试 `tests/serial_log/unit/test_log_keyword_catalog.py`（仍指向已删除的 `engines/agents` 路径）。
- **BREAKING**（契约口径）：关键词目录接口的取值来源由「配置文件」变为「数据库」，`keyword_file` / `updated_at` 字段语义随之变化；表格由三列变四列。接口路径、鉴权与信封不变。
- 二期另立变更（不在本单）：超管编辑 UI 与 HTTP 写接口；届时再放开「只读」红线。

## 关联文档

关联《PRD-平台总需求》§1.2 功能介绍第 6 条（验收证据：串口日志关键词命中）与 §3.2 数据业务流（串口日志）。该 PRD 为大纲体、无需求编号体系；本变更直接来源于需求方 2026-11-18 口头需求：「日志关键词变动写入数据库，新增范围字段（功能点 / 功能模块 / 关键词 / 范围），存量记录为通用，后续新增 H6601、H2234 等 SKU 专用范围」。

## Capabilities

### New Capabilities

（无——存储归属与范围语义并入现有 `serial-log-module` 能力，不新建能力目录。）

### Modified Capabilities

- `serial-log-module`: 「关键词对照表由串口日志模块组装」需求的取值来源由配置文件改为数据库；新增「串口日志拥有关键词对照表数据」需求（表归属、唯一写点、范围并集语义、迁移保留存量词条）。
- `device-log-keyword-catalog`: 表格由恰三列改为四列（新增「范围」）；取值来源与更新时间口径改为数据库；新增范围筛选；只读条款保持不变。

## Impact

- **后端**：`backend/apps/serial_log/`（`models.py`、建表迁移 + 数据迁移——编号实施时按 `serial_log` 最新迁移顺延，见 design.md D4；`api.py`、`keywords.py`）；`backend/config/device_log_keywords.json` 退役为种子档案。与实施中的 `add-serial-log-custom-ports` 无需求级重叠，迁移编号与同文件改动需按其落地状态协调（design.md Risks）。
- **前端**：`frontend/src/modules/serial-log/`（`api.ts` 类型、`helpers/log-keyword-rows.ts`、`constants.ts`、`components/LogKeywordPanel.vue` 及其样式）。
- **规格**：`device-log-keyword-catalog`、`serial-log-module` 两份 delta；`serial-log-page` 无需求级变化（其页面要求引用 catalog 规格，自动跟随）。
- **测试**：`tests/serial_log/{unit,api}`（迁移演练、目录契约、重写失效一致性测试）；`frontend/tests/serial-log/`（行构造、范围筛选、面板）。
- **规则变更申请（硬约束，先请示后动）**：前端 `frontend/src/modules/serial-log/AGENTS.md` 红线「关键词表只读……改表仍走 `DEVICE_LOG_KEYWORD_FILE` 指向的文件」中「改表走文件」一句需改为「改表走数据库（唯一写点 `serial_log/api.py`），页面仍只读」；后端 `backend/apps/serial_log/AGENTS.md` 职责与写库边界段同步登记新表。详见 design.md 的变更申请四要素。
- **不动的部分**：`engines/` 全部；`sl_log_ports` 与端口监听链路；采集写文件链路（`engines/uart_log` / `utils/logs`）；`DEVICE_LOG_KEYWORD_FILE` 配置与 `KeywordIndex.from_file` 保留作控制台兜底。
