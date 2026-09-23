## 1. 修复类型标注

- [x] 1.1 新增局部类型 `ElTreeNode = { data?: unknown }` 与收窄函数 `uiDataOf()`（校验 `type` / `key` 后返回 `UiTreeNode`），注释写明树数据恒由 `toUiNodes()` 构造、收窄点唯一
- [x] 1.2 `allowDrag` / `allowDrop` / `handleNodeDrop` 三个回调参数类型改为 `ElTreeNode`，函数体改用 `uiDataOf()`；判定逻辑与 emit 载荷零改动

## 2. 验证

- [x] 2.1 `cd frontend && npx vue-tsc --noEmit`：退出码 0、无输出（原为 3 处 TS2322）
- [x] 2.2 改模块定向单测（`tests/case-manager/p0/`）：**4/4 通过**（useProjects 2 项 + useCaseSheet 2 项）
- [x] 2.3 该文件的 `eslint`：0 error（1 条既有 warning `no-useless-assignment`，非本次引入）
- [x] 2.4 人工核对 diff：仅类型标注与取值方式变化，判定逻辑、事件语义、emit 载荷均未改动

> **验证范围说明**：按 `AGENTS.md` 行为规范第 2 条（测试范围收敛，禁止主动跑全量回归），本变更**未**运行 `npm test` 全量前端套件与 `vite build`，改用"类型检查 + 改动模块定向单测 + 该文件静态检查"这一最小集。该规则在本变更实施期间由用户新增。

## 3. 收尾

- [x] 3.1 `vue-tsc` 由 3 报错转为 0，本地门禁告警项 `vue-tsc` 具备转 PASS 的条件（实际转拦截在后续独立变更中执行）

---

## 结果记录（2026-09-23）

| 项目 | 修复前 | 修复后 |
| --- | --- | --- |
| `vue-tsc --noEmit` | 3 处 TS2322（均在 `ProjectTree.vue`） | **0 报错** |
| case-manager 定向单测 | — | 4/4 通过 |
| 改动文件 | — | `frontend/src/modules/case-manager/components/ProjectTree.vue`（+21 / −16 行） |
