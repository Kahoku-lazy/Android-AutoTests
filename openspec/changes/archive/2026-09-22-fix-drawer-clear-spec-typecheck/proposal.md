## Why

上一单 `add-drawer-clear-entry-test` 新增的 `frontend/tests/device-inspector/p0/SnapshotListDrawer.spec.ts` 留下 **2 条新增 `vue-tsc` 报错**：

`
tests/device-inspector/p0/SnapshotListDrawer.spec.ts(69,63): error TS2345
tests/device-inspector/p0/SnapshotListDrawer.spec.ts(70,65): error TS2345
`

原因是 `mockResolvedValue` 的入参未按本仓既有范式做 `as never` 断言（`ok(...)` 构造的 `{data:{status,data}}` 不是 `AxiosResponse`）。我在归档上一单时把这两条报错当成既有无关报错放过了 —— 这是**归档门禁漏判**，本单把它纠正过来。

## What Changes

- `SnapshotListDrawer.spec.ts` 的两处 `mockResolvedValue` 补 `as never`（与 `store.spec.ts` 的既有写法一致）。
- 不改任何产品代码、测试语义与生效规格。

## Capabilities

### Modified Capabilities

（无：只修测试文件的类型断言。）

## Impact

- 测试：1 个前端用例文件（2 处类型断言）
- 不涉及：产品代码、后端、规格
