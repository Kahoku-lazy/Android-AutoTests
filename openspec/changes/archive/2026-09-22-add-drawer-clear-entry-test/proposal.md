## Why

变更 `add-snapshot-retention-and-clear` 的任务 3.2 承诺「用例断言按键存在且空列表时不可用；确认文案含『不可恢复』」，但归档时只落了 store 侧用例（`clearSnapshots` 的成功/失败路径），抽屉自身的**二次确认**与**空态禁用**只有代码阅读、没有自动化验证。本单把这个缺口补上：**只加用例，不改产品代码、不改规格**。

## What Changes

- 新增 `frontend/tests/device-inspector/p0/SnapshotListDrawer.spec.ts`：覆盖「无快照时按键禁用且点击不发请求」「确认后只调一次清空端点且文案含『不可恢复』」「取消确认不发起清空」。
- 用例以 `el-button` 替身模拟 Element Plus 的「禁用不派发 click」语义（jsdom 不渲染 EP 真实组件）。

## Capabilities

### Modified Capabilities

（无：本单验证的是已生效要求 `device-inspector-page`「快照删除需二次确认」，不改变任何要求。）

## Impact

- 测试：新增 1 个前端用例文件（3 条）
- 不涉及：产品代码、后端、生效规格
