## Context

- 本仓前端用例的既有范式：`vi.mocked(api.fn).mockResolvedValue(ok(x) as never)`（见 `tests/device-inspector/p0/store.spec.ts`）。`as never` 是绕开 axios 响应类型的最小手段，不是新引入的写法。
- `vue-tsc --noEmit` 属前端关单门禁；上一单归档时它输出了 2 条 `tests/device-inspector/...` 报错，我误判为既有噪音。

## Goals / Non-Goals

**Goals:**

- 让 `vue-tsc` 恢复到「只有 3 条既有 `ProjectTree.vue` 报错」的状态。

**Non-Goals:**

- 不重构用例、不改产品代码、不动既有 3 条 `ProjectTree.vue` 报错（属他人范围）。

## Decisions

**D1 只在两处调用点补 `as never`。** 与 `store.spec.ts` 完全同形，避免为两行断言引入 mock 类型基建（超范围）。

**D2 门禁判定改为「全量输出逐条核对」。** 上一单的失误来自「按文件过滤 + 目视跳过」；本次直接看全量输出并逐条确认归属。

## 模块防火墙自检

- **产品代码**：零改动。
- **前端 HTTP 出口**：用例 mock `api.ts`，无新增调用。

## Risks / Trade-offs

- [`as never` 会掩盖真实的响应形状错误] → 本仓既有范式已如此；用例断言的字段形状由断言本身守住，不依赖类型。
