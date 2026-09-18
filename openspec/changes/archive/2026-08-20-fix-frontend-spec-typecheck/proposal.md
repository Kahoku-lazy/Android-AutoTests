## Why

`npm run typecheck`（vue-tsc --noEmit）在 test-runner 的 spec 文件上报 24 行既有类型债：① spec 对 api 函数直接挂 `.mockResolvedValue/.mockRejectedValue`（函数类型上无 mock 方法，需 `vi.mocked()` 包装）；② 任务字面量缺运行时被读写的字段（failedSteps/conclusion/_connectionHealthy 等）。虽 CI 只跑 vitest（行为 76/76 全过）、不影响产品代码，但 `build:check` 发布级检查长期红门禁侵蚀信任，且压在 Step 6 交付面上——收尾转绿。

## What Changes

- 仅修 `frontend/tests/test-runner/` 下 5 个 spec 文件的类型问题：
  - mock 断言改 `vi.mocked(fn).mockResolvedValue/...`（p0/p1 useTaskOperations）
  - 任务字面量补全运行时字段（p0 useQueuePoller / p0 p1 useTaskWebSocket）
- 不改任何产品代码、不改 vitest 行为语义（断言等价）

## 关联文档

- 纯测试类型修复，无 PRD/ARCH 关联；承接 OpenSpec 已归档 `2026-08-20-frontend-consume-authoritative-state`
- 无需求级行为变化

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯测试类型修复：`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- `frontend/tests/test-runner/p0/{useQueuePoller,useTaskOperations,useTaskWebSocket}.spec.ts`、`frontend/tests/test-runner/p1/{useTaskOperations,useTaskWebSocket}.spec.ts`
- 产品代码零改动；后端零改动
