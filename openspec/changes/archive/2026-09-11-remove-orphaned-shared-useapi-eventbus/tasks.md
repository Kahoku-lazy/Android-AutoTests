## 1. 删除前核实

- [x] 1.1 `\buseApi\b` 精确搜索 → `frontend/src` 仅命中 `useApi.ts` 自身的定义（第 18、22 行）；`frontend/tests` **0 处** → 无外部消费者（此前"有引用"是 `useApiGroupTree` 的子串误命中）
- [x] 1.2 `event-bus` 搜索 → `frontend/src` **0 处**；`frontend` 全量仅 3 处，全部在 `tests/PLAN-batch2-3modules.md`（旧计划文档）
- [x] 1.3 `bus.emit|bus.on|bus.off` 在 `frontend/src` **0 处** → 无隐式事件耦合在用

## 2. 删除

- [x] 2.1 删除 `frontend/src/shared/composables/useApi.ts`（53 非空行）
- [x] 2.2 删除 `frontend/src/shared/event-bus.ts`（2 非空行）
- [x] 2.3 验证 `shared/` 顶层（api/auth/components/composables/icons/styles/types + animations/api-auth-interceptors/api-client/ocrMatch）与 `composables/` 剩余 8 个符合预期

## 3. 门禁验证

- [x] 3.1 删除后复搜 → `useApi`（src）**0 处**、`event-bus`（src）**0 处**
- [x] 3.2 `node node_modules/vue-tsc/bin/vue-tsc.js --noEmit`（workdir: frontend）→ **35 条错误全部落在 6 个无关文件**（`tests/dashboard/*`、`device-inspector/store.ts`、`case-manager/components/ProjectTree.vue`），**提及被删文件的 0 条**
- [x] 3.3 `git status` → 本变更恰好 2 个 `D`，无其他改动混入
