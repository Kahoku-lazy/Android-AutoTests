## 1. 补用例

- [x] 1.1 新增 `frontend/tests/device-inspector/p0/SnapshotListDrawer.spec.ts`：挂载抽屉并断言「无快照时一键清空禁用、点击不弹确认也不发请求」。验证：`npx vitest run tests/device-inspector` 通过
- [x] 1.2 同文件断言「确认后只调一次清空端点，且确认文案含『不可恢复』」。验证：用例通过
- [x] 1.3 同文件断言「取消确认不发起清空」。验证：用例通过

## 2. 门禁

- [x] 2.1 前端门禁：`npx vitest run` 全绿、`npx vue-tsc --noEmit` 无新增报错。验证：与上一单的既有阈值一致
