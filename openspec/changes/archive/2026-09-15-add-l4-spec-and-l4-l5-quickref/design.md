## Context

L4（表格 / 卡片网格 / 表单）与 L5（覆盖层）是「布局区域与归属」表里唯二没有层速查的两层。L5 的契约已于上一变更沉淀为 `openspec/specs/frontend-l5-overlay/spec.md`（4 需求 / 7 场景）；L4 尚无 spec，也没有任何地方能读到「何时可以不用 `AppTable`」。

2026-09-14 实测（本变更全部数字的事实来源）：`AppTable` 4 消费方 / 原生 `el-table` 3 文件；分页 = 共享 `usePagination` 2 消费方 + `ReportDetail.vue` 手写 1 套；`el-form` 10 文件 / 46 个 `el-form-item`，`:rules` 命中 0，仅 `required` 11 处；`grid-template-columns` 47 处 / 23 文件；卡片零件 `AppCard` 9 文件、`KpiCard`/`SketchCard`/`DoodleNote` 12 文件。

## Goals / Non-Goals

**Goals:**

- 把 L4 契约规格化为 `frontend-l4-data-surface`（表格边界 / 分页唯一实现 / 表单校验口径 / 卡片与网格零件）
- 在 `frontend/AGENTS.md` 补齐 L4、L5 两节 6 段式速查，使 L0–L5 六层速查齐备
- 修正 L0 §⑥ 的失效计数，避免速查传播错误数字

**Non-Goals:**

- 不改任何前端代码：不做分页收敛、不迁移表单校验、不扩 `AppTable` API
- 不新增 L5 需求（复用既有 `frontend-l5-overlay`）
- 不重写 L0–L3 速查的既有内容

## Decisions

**D1 · 表单校验判据取 Element Plus `:rules` + `validate()`，而非把「手写 error ref」合法化**

EP 已内建校验，且项目已在用 EP 表单控件与全量 EP 样式；手写多个 `error` ref + 手动 focus 是把内建能力重做（违反「不要重复造轮子」），而 `required` 无 `:rules` 时只画必填星号、提交不校验，属误导性 UI。备选方案「承认手动校验为本层规范」会让 11 处误导 UI 永久合法化，不采纳。

**D2 · `AppTable` 的能力边界写进 spec，而不是本次扩展 `AppTable` API**

用户本次只选了「速查 + spec」，未选表格 / 分页收敛。扩 API 需要真实诉求与浏览器验证，属另一变更；本次把「何时可绕过」定成可验收判据，并把 3 处例外逐一点名。

**D3 · 分页只登记债，不本次收敛**

同 D2。`report-generator/ReportDetail.vue:32-135` 的手写分页登记为例外，spec 只约束「不得出现第 4 套」，不要求本次删除既有实现。

**D4 · L5 不新增 spec，速查复用 `frontend-l5-overlay`**

L5 契约上一变更已规格化并经归档；再写一份会造成双真相源。L5 速查只做「人读版复述 + 指向真相源」。

**D5 · 修正 L0 §⑥ 的 EP 导入计数**

L5 速查需要复述「EP 全量样式」口径，若引用的计数是错的，速查会把错误传播下去。原文「30 个文件是显式 `import { ElMessageBox }`」把两类混为一谈：实测显式 `from 'element-plus'` 为 36 文件、`import { ElMessageBox }` 为 17 文件（2026-09-14）。

## 模块防火墙自检

- 跨 App import：不涉及。本变更只改 `frontend/AGENTS.md` 与 `openspec/` 文档，无代码 import 变化
- 禁止跨 App import service / runner / consumer / state_machine：不涉及
- 所有 INSERT / UPDATE / DELETE 收敛到各 App 的 api.py：不涉及，无后端写操作
- 前端不直连数据库；仪表盘不做写操作：不涉及，不改任何 `api.ts` / HTTP 调用
- 新增跨模块依赖：无

## Risks / Trade-offs

- [速查里的绝对计数会随代码演进过期] → 每条计数标注实测日期（2026-09-14）并给出复核命令；破约项以 `rg` 命中数为判据而非硬写数字
- [登记为例外可能被读成「永久合法」] → 在 spec 场景中写明上限语义（`SHALL NOT` 扩散到第 4 处 / 新增第 4 套），把例外定义成上限而非许可
- [表单判据与前 11 处现状不一致] → 明确登记为已知缺口，且只约束新增 / 修改的表单，本次不动既有代码
- [L4 与 L5 速查可能和 `frontend/AGENTS.md` 顶部的「布局区域与归属」表口径打架] → 速查只展开表里已有的两行，不新增层定义；冲突时以表 + spec 为准并在速查中标注真相源

## Migration Plan

- 无数据 / 代码迁移，纯规格与文档变更；回滚为 revert 本变更提交
- 验证顺序：`openspec validate --strict` → `rg` 逐条复核速查计数 → `openspec archive`
