# Design: align-backend-docs-with-code

## Context

动机与逐条清单见 proposal.md；漂移证据见审计报告第七节。约束：文档以**现行代码与已归档决策**为真相源，只改文本不改行为；红线条款修订已获需求方批准（变更申请四要素记录在 proposal）。

## Goals / Non-Goals

**Goals**
- 六个层面（apps AGENTS / app AGENTS / ARCH / PRD / 活跃 spec / tests 文档）与代码一致；空 AGENTS 补齐；失实红线删除。

**Non-Goals**
- 不改任何运行逻辑（ops __all__ 两行补全除外）；不重写 test_channels（归属变更②任务 1.5）；不动钱口径代码（变更⑥）；不新增规则——只把既有规则表述改准确。

## Decisions

### D1 分两组提交，按依赖定合并时序
A 组（描述现状的全部文档 + frontend ai-assistant 红线修正 + spec 退役）先合并，解锁变更②7.1；B 组（device_pool AGENTS）描述收敛后架构，待变更④合并后合并。理由：避免「文档超前代码」制造新漂移。备选：一次性合并——device_pool 段会失真，弃。

### D2 公开路径表述改「真相源 + 列举」双层
apps/AGENTS 不再手抄路径清单作唯一依据，改为「以 _is_public() 为准」并附当前列举（含三条旁路）。理由：手抄清单已漂移过一次，真相源指向代码才止漂。

### D3 usage_ledger 厂商红线与钱口径变更的分工
本批改红线 2 文本（三类厂商，与 normalize_provider/rates 现状一致）；变更⑥只改计费代码与 token 提取，不重复改文档。两单在 proposal 互相登记，避免双改冲突。

### D4 新建 AGENTS 的最小内容
device_pool/dashboard/case_manager/knowledge_search 四份按「职责 + 红线 delta + 依赖方向 + 关单附加项」最小骨架写，内容全部取自现行代码事实（审计已核），不发明新规则。knowledge_search 的 View 编排越权（审计 R-4）在 AGENTS 中先如实登记「编排下沉 api 为待偿债权」，不假装已合规。

## Risks / Trade-offs

- [文档批与在途变更（assistant-author 等）改同一 AGENTS] → 合并前 git pull 核对；三个在途变更均不触碰本批文件（已核 deltas 目录）。
- [ARCH/PRD 改动面大] → 只改 WS/语音相关段落，逐段 diff 可追溯，不顺手重写无关章节。

## Migration Plan

纯文档，无部署动作。回退 = 还原文档提交。spec 退役经 OpenSpec archive 正常收口（REMOVED delta 带 Reason/Migration）。

## Open Questions

无。