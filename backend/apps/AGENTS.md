# backend/apps 索引 — 模块文档导航

> **层级**：根 `AGENTS.md` → `backend/AGENTS.md`（后端全局约束）→ **本文件（索引）** → `.agents/docs/apps/**`（模块文档）
>
> 本文件**不承载规则**，只做导航。**进入某个模块改代码前，先读下表列出的文档**；
> 文档里的红线、契约、依赖方向与关单附加项，效力等同模块级约束。

## 怎么用

1. 先读 [backend/AGENTS.md](../AGENTS.md)：分层、写库路径、响应信封、HTTP/WS/AI 协议要点、关单清单。
2. 定位要改的模块 → 读下表对应文档（一个模块可能有多篇，按功能域分开）。
3. 跨模块改动 → 两个模块的文档都要读；依赖方向以 `backend/AGENTS.md` §1.1 与各模块文档为准。
4. 命令级细节（check / pytest / ruff / OpenAPI / 迁移演练）→ [self_test_and_checks.md](../../.agents/docs/apps/self_test_and_checks.md)。

## 模块 → 文档

| 模块 | 文档 | 讲什么 |
|------|------|--------|
| accounts | [accounts_session_and_logout.md](../../.agents/docs/apps/accounts/accounts_session_and_logout.md) | `sid` 会话标识、登出即作废整会话、续期透传、吊销 TTL 与落库、fail-closed |
| accounts | [accounts_username_uniqueness.md](../../.agents/docs/apps/accounts/accounts_username_uniqueness.md) | 唯一性以 DB 约束为权威、409 映射、savepoint 必要性 |
| accounts | [accounts_paths_and_errors.md](../../.agents/docs/apps/accounts/accounts_paths_and_errors.md) | 尾斜杠约定（缺斜杠 404）、五个端点错误码表、鉴权姿态 |
| ai_assistant | [ai_assistant_agent_config_and_cards.md](../../.agents/docs/apps/ai_assistant/ai_assistant_agent_config_and_cards.md) | Agent/模型配置、助手名片表、对话快照、SOP 不读对话栏、写库入口在 `api.py`、实现在 `services/` |
| bug_manager | [bug_manager_bug_ticket_ledger.md](../../.agents/docs/apps/bug_manager/bug_manager_bug_ticket_ledger.md) | `bug_tickets` 台账、三类问题提取、红线表、双向依赖口径 |
| ops_console | [ops_console_user_management.md](../../.agents/docs/apps/ops_console/ops_console_user_management.md) | 11 个运营端点与权限、经 `accounts.api` 写库、不能动自己/超管/运营、注销只删账号 |
| report_generator | [report_generator_report_inventory.md](../../.agents/docs/apps/report_generator/report_generator_report_inventory.md) | 只读报告台账、列表数据源与限量、正文不在此 App、退役端点禁复活 |
| serial_log | [serial_log_port_management.md](../../.agents/docs/apps/serial_log/serial_log_port_management.md) | 端口登记双轨制、单端口增量生效、采集在引擎层、接口与权限 |
| serial_log | [serial_log_keyword_table.md](../../.agents/docs/apps/serial_log/serial_log_keyword_table.md) | 关键词真相源是 `sl_log_keywords`、通用与专用并集、JSON 已退役为种子 |
| task_list | [task_list_task_lifecycle.md](../../.agents/docs/apps/task_list/task_list_task_lifecycle.md) | 五张任务表、执行链到 `backend_bridge`、计费走 `task_cost`、依赖方向 |
| usage_ledger | [usage_ledger_usage_billing.md](../../.agents/docs/apps/usage_ledger/usage_ledger_usage_billing.md) | 账本模型、`rates.py` 基数 + `pricing.py` 公式、厂商三类、六条红线 |
| knowledge_search | [knowledge_search_retrieval.md](../../.agents/docs/apps/knowledge_search/knowledge_search_retrieval.md) | 四张表、七个端点、评测批次状态机、检索实现、View 编排待偿债权 |
| device_pool | [device_pool_write_boundaries.md](../../.agents/docs/apps/device_pool/device_pool_write_boundaries.md) | 10 个端点、current 指针语义、GET 副作用、锁模型与 observe 链、写库收敛现状与目标 |

## 跨模块命令与门禁

[self_test_and_checks.md](../../.agents/docs/apps/self_test_and_checks.md) —— Django 自检、单元/集成/接口测试、
代码风格、架构边界、OpenAPI 校验、迁移演练的完整命令集。

## 暂无模块文档的目录

| 目录 | 现状 |
|------|------|
| `case_manager` | 无模块文档 |
| `dashboard` | 无模块文档 |

这两个目录下的改动，按 `backend/AGENTS.md` 全局约束执行；需沉淀模块口径时新增
`.agents/docs/apps/{app}/{app}_{feature}.md` 并回到本表登记。
