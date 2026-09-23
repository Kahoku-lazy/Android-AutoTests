## Context

- **待退役链路（唯一活路径）**：`apps/device_inspector/urls.py:24` → `views.py:118-125 snapshot_analyze` → `api.py:514-522 analyze_snapshot` → `service.py:254-266 analyze_snapshot_payload` → `algorithms/layout.py:107 classify_structure`。
- **无产品入口（实测）**：`frontend/src` 全目录 `grep analyze` = 0；`apps/ai_assistant/tools.py:419-432` 的 11 个工具无页面分析；`grep _inspector_analyze` 只命中 `openspec/changes/archive/**`（历史归档）。
- **零测试**：`grep classify_structure tests/` = 0；无 `test_layout*.py`。
- **语义层同样孤儿**：`apps/ai_assistant/llm_semantic.py:19 validate_semantic` 零调用方（`grep validate_semantic apps/` 只命中自身）、零测试（`tests/ai_assistant/` 不存在）。
- **规格现状**：`openspec/specs/page-analysis-semantic` 共 5 条需求（纯规则结构分析独立可用 / 元素功能名命名 / 语义提交校验 / 页面意图总结 / 卡片角色识别），全部只由上述两处载体支撑。
- **端点全集**：接口文档原写「9 个端点」（`API-设备检查器.md:3`），退役后为 8 个。
- **守护**：`tests/graybox/unit/test_api_path_callers.py` 的 yaml 面下限 42（实测 45）；本变更删 2 条 `path:`，实测将降至 43，仍高于下限。

## Goals / Non-Goals

**Goals:**

- 第一代 6 层分区算法、其端点与孤儿语义层同批归零，规格与实现对得齐。
- 文档（接口文档 / PRD-03 / 总体架构图）不再描述已不存在的端点与模块。

**Non-Goals:**

- 不动分层查询端点与其算法（`element_layers` / `xpath` / `hierarchy` / `vision/ocr`）。
- 不改前端（前端早已不含该端点调用）。
- 不处理 `ai-platform-task` 规格中 `analyze_page` / `save_page_semantic` 的既有漂移。
- 不做 PRD-03 的整体刷新。
- 不留兼容期、不做重定向。

## Decisions

**D1 删端点，而不是保留端点只登记「无入口」。** 依据：端点没有任何产品入口、零单测，且其算法模块与前端实现已分叉（前端消费 `layers`）。保留它意味着长期维护一份只有接口用例 401/404 在跑的代码，并让 `page-analysis-semantic` 继续以「前端按钮与 AI 工具」为名义挂着 —— 而这两个用途都已不存在。备选：保留端点、只改规格登记缺口 → 否决（用户已确认「一并退役」；保留会让规格里的人称与实现对不上）。

**D2 用 `REMOVED Requirements` + `retire_capabilities: true` 退役能力。** 该 spec 5 条需求随载体一起归零，归档流程会删除主 spec，不留空壳。依据：`openspec` 无 `spec remove` 子命令；`retire_capabilities` 是「移除最后一条需求」的必需显式开关（防误删设计），先例见已归档的 `retire-device-session-spec` 与 `remove-element-locator-web-api`。备选：直接删 `openspec/specs/page-analysis-semantic/spec.md` → 否决（绕过归档流程，规格库与变更记录脱钩）。

**D3 同批删 `llm_semantic.py`。** 它是该能力「语义提交校验 / 功能名命名 / 页面意图总结 / 卡片角色识别」4 条需求的唯一实现，零调用方零测试。保留会留下一个「跑不到、也没人 import」的模块，而且它的存在会让人误以为语义提交通道还在。备选：保留 → 否决（与「规格与实现对得齐」相反）。

**D4 文档只做「本变更使其失效」的最小修正。** 接口文档是端点契约的登记处，必须同步（9 → 8、删第 6 节、重新编号、修正「第 N 节」引用）；PRD-03 只修端点契约、代码指针、2 条 TC 行与「五类来源」计数。PRD-03 的 §结构分析 整体仍按第一代分区叙述（分区筹码、筛选、固定 7 行），那是既有漂移，不在本变更内 —— 只做局部替换会让该节半新半旧，故明确登记为遗留缺口（见 Risks）。备选：顺带把 PRD-03 刷新为「元素分组」口径 → 否决（超出范围，且需要先补一份 `layers` 的 PRD 章节，属独立变更）。

**D5 不新增兼容期与重定向。** 端点是内部接口、无外部消费方，且`APPEND_SLASH=False` 下子路径本就会 404；加一层告警或空壳端点只会留下第二份真相。备选：保留一个返回 410 的空壳 → 否决（无消费方需要迁移提示）。

## 模块防火墙自检

- **View 只分发**：删除视图后 `views.py` 仍只调 `api.*`；不新增直连 ORM。
- **跨 App**：`ai_assistant/llm_semantic.py` 是纯校验模块（不 import 其它 App 内部实现、不写库），删除不影响 `apps/AGENTS.md` 的写库收敛。
- **算法层依赖**：删除后 `algorithms/` 仍是零 `apps.*` / 零 `django.*`；抽查 `--check-boundaries`。
- **前端 HTTP 出口**：零改动（本就不调用该端点）。

## Risks / Trade-offs

- [外部/脚本调用该端点会得到 404] → 已核实仓内无消费方（前端 0 命中、AI 工具 0 命中、测试仅 2 条 401/404 用例且一并删除）；端点从未出现在前端 API 层。
- [PRD-03 §结构分析 仍按第一代分区叙述，本次只做局部修正，该节半新半旧] → 已登记为遗留缺口并在变更的「明确移出本变更范围」写明；PRD-03 需要一次独立刷新（含补 `layers` 章节）。
- [`ai-platform-task` 规格仍提 `analyze_page` / `save_page_semantic`] → 该漂移先于本变更（工具在注册表中本就不存在），本次只在报告与范围说明中登记，不误判为本变更引入。
- [`test_api_path_callers.py` 的 yaml 面实测下降 2 条] → 下限 42 仍有余量；若实测跌破，按先例以「本变更删除 2 个调用点」为由重登记下限，不改扫描器。
- [接口文档中 `page-analysis-semantic` 之外仍残留别的第一代描述（第 548 行称元素来自 `models/ui_nodes.Node`）] → 既有漂移，本变更不顺手改。

## Migration Plan

- 一次提交内完成：删文件 → 删路由/视图/api/service → 删接口用例 → 改规格 delta → 同步文档。
- 回滚：`git revert`（无 DB 变更、无数据迁移，无不可逆副作用）。

## Open Questions

无。
