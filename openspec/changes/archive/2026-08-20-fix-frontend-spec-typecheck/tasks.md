## 1. p0 spec 类型修复

- [x] 1.1 `p0/useQueuePoller.spec.ts`：任务字面量补 runId 等运行时字段；验证 `npx vue-tsc --noEmit` 该文件错误归零
- [x] 1.2 `p0/useTaskOperations.spec.ts`：mock 断言改 `vi.mocked()` 包装 + 字面量补 failedSteps；验证同上
- [x] 1.3 `p0/useTaskWebSocket.spec.ts`：字面量补 _lastHeartbeat/_connectionHealthy/failedSteps/conclusion；验证同上

## 2. p1 spec 类型修复

- [x] 2.1 `p1/useTaskOperations.spec.ts`：mock 断言改 `vi.mocked()`；验证同上
- [x] 2.2 `p1/useTaskWebSocket.spec.ts`：字面量补 _connectionHealthy/_wsJustReconnected；验证同上

## 3. 门禁

- [x] 3.1 `npx vitest run tests/test-runner` → **76/76 全绿**（修 1 处回归：useQueuePoller 跳过用例的 runId 字面量改 `undefined` 保持原断言语义）
- [x] 3.2 `npm run typecheck` 我方区域（test-runner/report-generator）错误 **0 行**（修复手法：`vi.mocked()` 包装 + `as never` 参数断言 + 字面量补字段；全量其他区域错误不属本变更）
