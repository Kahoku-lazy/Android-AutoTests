## 1. 修类型断言

- [x] 1.1 `SnapshotListDrawer.spec.ts` 的两处 `mockResolvedValue` 补 `as never`。验证：`npx vue-tsc --noEmit` 全量输出中不再出现 `tests/device-inspector/` 的报错
- [x] 1.2 用例语义不变：`npx vitest run tests/device-inspector` 仍全绿。验证：3 个文件 16 条用例通过

## 2. 门禁

- [x] 2.1 前端门禁：`npx vitest run` 全绿；`npx vue-tsc --noEmit` 仅剩 3 条既有 `ProjectTree.vue(430/431/434)` 报错。验证：全量输出逐条核对
