## 1. L4 能力规格

- [x] 1.1 写 `openspec/changes/add-l4-spec-and-l4-l5-quickref/specs/frontend-l4-data-surface/spec.md`（4 需求 / 8 场景：表格首选与登记例外、分页唯一实现、表单校验走 EP rules、卡片与网格零件）；验证：`openspec validate --strict` 通过且四条需求各含场景

## 2. frontend/AGENTS.md 速查补齐

- [x] 2.1 在「L3 层速查」之后新增「### L4 层速查：表格 / 卡片网格 / 表单」（6 段式：元素链 / 代码范围 / 能写什么 / 不能写什么 / 契约与验收 / 破约如何被发现），② 列 `AppTable` · `usePagination` · `el-form` · 卡片零件，④ 写「何时可绕过 AppTable」「`:rules` 口径」「不得另建通用表格 / 分页 / 卡壳」，⑥ 给 `rg` 判据并登记 3 类已知缺口；验证：体例与 L0–L3 速查一致，计数与本变更实测一致
- [x] 2.2 新增「### L5 层速查：覆盖层（阻塞 / 非阻塞）」（6 段式），行为真相源指向 `openspec/specs/frontend-l5-overlay/spec.md`，⑥ 记录「原生 `confirm` 已归零 / 自建遮罩已归零」与现存缺口（`el-drawer` 无皮肤、弹层属性三套写法）；验证：内容与 `frontend-l5-overlay` spec 无冲突、不新增需求
- [x] 2.3 修正 L0 §⑥ 的失效计数为「显式 `from 'element-plus'` **36 文件** / `import { ElMessageBox }` **17 文件**（2026-09-14 实测）」；验证：`rg` 复核与实测一致
- [x] 2.4 逐条复核速查内所有计数（`AppTable` 4 / `el-table` 3 / 分页 2+1 / `el-form` 10·46·0·11 / grid 47·23 / `AppCard` 9 / KPI 等 12 / `el-dialog` 17 / `el-drawer` 2 / `ElMessage` 26 / `ElMessageBox` 17 / 原生 `confirm` 0 / 自建遮罩 0）；验证：每条 `rg` 命中数与速查一致

## 3. 门禁与归档

- [x] 3.1 `openspec validate add-l4-spec-and-l4-l5-quickref --strict`；验证：exit 0
- [x] 3.2 归档（经 `openspec-archive-change`）；验证：`openspec/specs/frontend-l4-data-surface/spec.md` 存在，变更进入 `openspec/changes/archive/2026-09-14-add-l4-spec-and-l4-l5-quickref/`
