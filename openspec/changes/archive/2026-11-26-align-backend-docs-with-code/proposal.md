# Proposal: align-backend-docs-with-code

## Why

审计确认成体系的文档漂移：AGENTS/ARCH/PRD/活跃 spec/测试文档六个层面仍描述已退役状态（WS 生产点、公开路径、计价路径、厂商口径、任务执行链、端点清单），多个归档变更声称删除的物件实际残留。这类漂移会直接误导后续 AI 与人工开发（本次审计即发现子代理与技能描述被过期文档误导的实例）。需求方已批准 D-DOC 红线文档批变更申请。

## What Changes

**红线变更申请四要素（已获需求方批准，2026-11-19）：**
- **改什么**：把下列规则/架构文档改成与现行代码及已归档决策一致；无行为变化。
- **为什么必须改**：文档是 AI 与人工开发的准入依据，失真文档持续产生错误决策（审计实证）。
- **影响面**：仅文档与规格文本；不改任何运行代码逻辑（test_channels 失效断言除外，见下）。
- **怎么回退**：还原文档提交即回旧文本。

具体清单：
- **后端约束上移（2026-11-23 需求方追加）**：`backend/apps/AGENTS.md` → `backend/AGENTS.md`，约束面由 `apps/` 扩到整个 `backend/`（`apps/`、`gateway/`、`shared/`、`config/`、`models/`）。改什么/为什么/影响面/回退：文档路径与适用范围，因该文件本就写平台级分层与协议，放在 `apps/` 下对 `gateway/` 无约束力；影响 13 文件 14 处引用（已同步）；回退 = 文件移回并还原引用。**未新增任何依赖边界条款**（§1.1 条文原样保留，如需为 `gateway/` 立边界，另起变更申请）。
- **模块文档外置（2026-11-23 需求方追加，已执行）**：8 个 app 的 `AGENTS.md` 内容按功能域改写成 11 篇模块文档，落在 `.agents/docs/apps/{app}/{app}_{feature}.md`（英文名）；`backend/apps/AGENTS.md` 改为**纯索引**（模块→文档表）；`backend/apps/自测与检测指令.md` 迁为 `.agents/docs/apps/self_test_and_checks.md`（改名）；11 个 app 级 `AGENTS.md`（8 个有内容 + 3 个 0 字节）全部删除。四要素：**改什么**＝文件布局与命名；**为什么**＝模块口径原与"约束"耦合在 `AGENTS.md`，既无法按功能分篇、也无法被索引按需加载；**影响面**＝仅文档与引用，无代码逻辑；**回退**＝还原该批文件即回旧布局。
- **三棵树同步外置（2026-11-23 需求方追加，已执行）**：`frontend/`（15 篇）、`tests/`（4 篇）、`engines/`（12 篇）同样改为「索引 + 外置文档」，源 AGENTS.md 共删 22 个（含 4 个 0 字节）；`engines/AGENTS.md` 保留为索引（`engines-agents-style-check` 靠它定位仓库根）。另修 `.gitignore:114` 的 `docs/` → `/docs/`，否则 `.agents/docs/**` 全部被忽略、索引链接在干净 clone 上失效。
- **WS 生产点收口**：`backend/AGENTS.md` §2 WS 段改「当前 0 生产点，新增先走 OpenSpec」；ARCH-平台架构设计.md、PRD-平台总需求.md 对应段同步；**退役活跃规格 knowledge-assistant-voice**（归档 tasks 声称已删实际仍在，本变更以 REMOVED delta 正式收口）。
- **公开路径真相源**：`backend/AGENTS.md` 身份段改为「以 gateway/middleware._is_public() + 三条显式旁路为准」并列举（/api/auth/login|register|refresh、/admin/、/static/、/media/、/api/schema/、/api/swagger/；旁路：RETIRED_AUTH_PATHS、log ticket、DRAIN 回环）。
- **task_list/AGENTS.md**：删已下线的 report 端点宣称；执行链改「task_runner → backend_bridge → 引擎；计费 task_cost + usage_ledger」；依赖方向改「读 AssistantRelease 与 sop workflow api」（AIAgent/filter_agents_for_user/resolve_assistant_name 均已不存在）。
- **ai_assistant/AGENTS.md**：「写库只在 api.py」改「写库入口只经 api.py，内部写库层在 services/」。
- **usage_ledger/AGENTS.md**：计价路径改「DeepSeek 等走 rates.py，pricing.json 兜底；engines 仅借高峰规则」；红线 2 厂商口径改三类（deepseek/dashscope/openai 兼容，含 grok 展示名）；文件表补 rates.py。**注**：厂商红线条款与 fix-eval-usage-billing 的钱口径变更申请重叠，以本批文档先行、钱口径变更不重复改文档。
- **bug_manager/AGENTS.md**：问题分类改三类（补 requirement_breakdown）；依赖方向补 TaskEvent 只读。
- **ops_console/AGENTS.md + views.py 端点清单 docstring**：补 model-grants/grant-author/revoke-author/grant-operator/revoke-operator；写口清单补 ai_assistant.api 四授权函数；api.__all__ 补 set_model_use/set_assistant_author（代码一行，属清单一致性）。
- **accounts/apps.py docstring**：「没有自有表」改「acc_token_revocations 吊销落库」。
- **apps/__init__.py docstring**：「5 existing + 2 planned + 3 reserved」改 12 个 app 现状。
- **空 AGENTS 补齐**：device_pool（写库层=api.py，**须待变更④合并后按收敛后架构写**）、dashboard（纯只读聚合 app）、case_manager（行表 CRUD/导入/编译契约）；knowledge_search 新建 AGENTS.md（检索/评测/设置契约与 View 分发纪律）。
- **frontend ai-assistant/AGENTS.md**：删失实红线「agents.ts 与 TASK_KIND_* 仍被 task-list 引用」（审计证实 task-list 零 import）——**本项须先于变更②的 7.1 合并**。
- **tests/AGENTS.md**：迁移状态表删 knowledge/、engines/agents/ 行，补 engines/ae_harness、backend_bridge 现状；自测与检测指令.md 业务 marker 删已退役 test_runner。
- **失效架构测试修复**：tests/arch/unit/test_channels.py TestAgentScopeChannel 断言改「engines/agents 不得存在」（与 check_gates 退役门禁一致），docstring 同步（此项已并入变更②任务 1.5，本变更不重复执行，仅登记归属）。

## 关联文档

无新增 PRD 需求编号——文档对齐变更（D-DOC 批）。问题来源为后端审计报告第七节 DOC-1~DOC-13 与前报告 B4/C1/C3/S1 组；需求方已批准红线变更申请打包。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `knowledge-assistant-voice`: 整体退役——唯一 requirement「知识库语音经 workflow 出口接入」随知识助手下线（retire-engines-agents）移除，WS 路由空清单由退役门禁守护。

## Impact

- **文档**：backend/AGENTS.md、backend/apps/AGENTS.md（改为模块文档索引）、.agents/docs/apps/**（11 篇模块文档 + self_test_and_checks.md）、accounts/apps.py、apps/__init__.py、ops_console/views.py docstring、frontend/src/modules/ai-assistant/AGENTS.md、tests/AGENTS.md、dev_docs/ARCH_PRD/ARCH-平台架构设计.md、PRD-平台总需求.md。
- **规格**：openspec/specs/knowledge-assistant-voice 经 REMOVED delta 退役。
- **代码**：仅 ops_console/api.py `__all__` 两行补全（清单一致性，无行为变化）。
- **合并时序**：A 组（除 device_pool AGENTS 外全部）先合并 → 解锁变更②7.1；B 组（device_pool AGENTS）待变更④合并后合并。