## Why

L2（页头区 / 页面根区）的行为与结构契约已在 `fix-l2-page-region` 与 `fix-l2-structure` 两个变更中收敛并归档，主 spec `openspec/specs/frontend-l2-page-region/spec.md` 已含 9 条契约；但 `frontend/AGENTS.md` 只有「L0 层速查」与「L1 层速查」两节，**没有 L2 层速查**。结果是：接手者（人或 AI）知道 L0/L1 的边界，却没有任何地方能一次读到「新页面根该怎么写、页头能不能自建、内边距取哪个值」。本变更把已收敛的 L2 结构沉淀为第三节速查，让 L0/L1/L2 三层速查对齐。

## What Changes

- 在 `frontend/AGENTS.md` 的「L1 层速查」之后、「跨模块共享文件：`shared/`」之前，新增「### L2 层速查：页头区 / 页面根区」，体例与 L0/L1 速查对齐（① 元素链 ② 代码范围 ③ 能写什么 ④ 不能写什么 ⑤ 契约与验收 ⑥ 破约如何被发现）。
- 内容只**复述**已归档的契约与 `fix-l2-structure` 的实际落点，并写明行为真相源指向 `openspec/specs/frontend-l2-page-region/spec.md`；不引入任何新规则。
- 在 ⑥ 记录 3 条真实存在的已知缺口：A/C 类模块 scoped `.doc-page { height:100% }` 是死声明、`workflow/index.vue` 的页面根不用 `--fixed` 且主体是 `.wb-body`（画布页例外）、`.soft-icon*` 家族已无消费方。
- **BREAKING**：无。纯文档变更，不改任何代码、行为、接口或测试。
- **不改** `frontend/AGENTS.md` 中「规则唯一真相源：`.agents/skills/android-autotests-rules/references/frontend.md`」这句**失效引用**（该目录已在工作区删除）——仅在结论里点出，避免夹带范围外改动。

## 关联文档

- `openspec/specs/frontend-l2-page-region/spec.md`：9 条契约（5 行为 + 4 结构），本节的真相源
- `openspec/changes/archive/2026-09-14-fix-l2-page-region/`、`.../2026-09-14-fix-l2-structure/`：本节所述落点的实施与实测记录
- `dev_docs/05-开发与测试/设计方案与报告/报告-前端区域层级与L2现状复盘.html`：结构全貌与现状复盘（人读版）
- `frontend/AGENTS.md` 既有的「L0 层速查」「L1 层速查」：本节体例来源
- 说明：`dev_docs/文档编号对照表.md` 不存在；`.agents/skills/android-autotests-rules/` 已在工作区删除，故本次无规则真相源可同步

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无；纯文档变更，`.openspec.yaml` 已声明 `skip_specs: true`）

## Impact

- **文档**：`frontend/AGENTS.md` 新增一节（约 60 行，与 L0/L1 速查同量级）
- **不影响**：任何前端代码、`openspec/specs/`、API 契约、路由表、测试与构建
