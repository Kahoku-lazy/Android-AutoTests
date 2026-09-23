## Context

- 动机与漂移清单见 `proposal.md`（Why），此处只记影响做法的事实与边界。
- **PRD-03 的定位**：`dev_docs/ARCH_PRD/` 下的模块需求文档；按根 `AGENTS.md`，功能需求入口从 `PRD-需求总纲` 开始，PRD-03 是设备检查器的需求落点。它同时承载「产品功能」（UI交互 / API契约 / 数据表单）与「测试」（业务场景 / 用例 / 覆盖）两大部分。
- **规格真相源**：`openspec/specs/device-inspector-page`（页面呈现与交互）、`device-inspector-layers`（分层查询契约）、`device-inspector-snapshots`（采集与索引）、`element-layering`（分组与主定位口径）。刷新后必须与这四份一致，不得另立口径。
- **代码真相源**（取证面）：`frontend/src/modules/device-inspector/{api.ts,constants.ts,store.ts,index.vue,components/**}`、`apps/device_inspector/{urls.py,views.py,api.py,service.py}`、`algorithms/element_layers.py`、`tests/**`。
- **文档状态**：PRD-03 在当前工作区**未被 git 跟踪**（`??`），故本变更的 diff 不出现在 `git diff` 里，只能靠逐条 read 核对。

## Goals / Non-Goals

**Goals:**

- PRD-03 的每一处口径都能在代码或规格里找到依据；把「描述已删除能力」的段落换成描述当前能力的段落。
- 补齐缺失的「分层查询」需求章节（此前规格有、PRD 无）。
- 测试一节如实反映当前资产，不再宣称「灰盒单元层、集成层为 0」。

**Non-Goals:**

- 不改任何代码、接口、规格、测试。
- 不新增需求（不借刷新之机把「应该有的行为」写进需求）——只描述**已有**行为。
- 不改 `ARCH-平台总体架构.md` 与 `多智能体编排-最终骨架设计.md`（理由见 proposal 的「明确移出本变更范围」）。
- 不顺手修 PRD-03 之外的文档（接口文档已在 `retire-legacy-page-partition` 同步）。

## Decisions

**D1 只描述已有行为，不借刷新补需求。** 依据：需求文档刷新容易夹带「顺手把想要的写进去」，那会让 PRD 与规格再次分叉（规格才是需求真相源，改需求要走 spec delta）。故判据是「PRD 的每一句都能指向一处代码或一份规格」，而不是「PRD 读起来完整」。备选：把刷新当成一次需求修订 → 否决（本变更声明 `skip_specs`，夹带需求即与声明矛盾）。

**D2 「结构分析」改名为「元素分组（分层查询）」。** 依据：该节内容整体换成两级分组与分层查询；留着旧标题会让读者以为「结构分析」这个能力还在。备选：保留标题只换内容 → 否决（标题是检索入口）。

**D3 分区 → 分组逐处核对，不做全局文本替换。** 依据：「分区」在 PRD 里既指已退役的 6 层分区，也被用作普通词；逐处判断，避免把仍在使用的表述改坏，也避免掩盖语义变化。备选：全局替换 → 否决。

**D4 快照详情端点的「无前端调用方」写进附录缺口，而不是删端点。** 依据：本变更声明 `skip_specs` 且不改代码；端点去留是产品决定（与 `retire-legacy-page-partition` 同类），先如实登记。备选：本次顺手退役 → 否决（超范围，且要动接口用例、`api.py` 白名单与接口文档）。

**D5 两处历史记录不动。** 依据见移出范围：`ARCH-平台总体架构.md` 自述对应 commit `300471d6`；那份 AgentScope 笔记是 2026-08-28 的实现复盘，其描述的 `agent_scope/` 目录在当前仓库已不存在（真实实现在 `engines/ai/agentscope/`），只删一行 `llm_semantic.py` 并不能让它变对。备选：按当前代码重写该笔记 → 否决（属该笔记自身的维护，且其「复盘」性质本就绑定当时的实现）。

## Risks / Trade-offs

- [刷新时把某处旧口径当现行口径照抄] → 每节落地前用 read / grep 指向 `路径:行号` 取证；取证不到的表述不写。
- [PRD 与规格再次分叉] → 分层查询一节以 `device-inspector-layers` 的需求为骨架写，不另造字段。
- [PRD-03 未被 git 跟踪，改动不留 diff 痕迹] → tasks 的验收留痕里逐节列出改后的章节标题与关键句，便于复核。
- [并发的其他会话同时在改 device-inspector 前端] → 本变更只读前端代码；若读到的行为与刷新结果冲突，以刷新当时实测为准并在留痕中写明。

## Open Questions

无。
