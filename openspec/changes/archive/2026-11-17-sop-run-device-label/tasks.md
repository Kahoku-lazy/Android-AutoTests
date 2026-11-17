## 1. 文案

- [x] 1.1 改 `frontend/src/shared/helpers/device-address.ts` 的 `deviceLabel()`：在线设备只输出「地址 · 型号」，`status` 存在且不是 `ONLINE` 时才追加 `(STATUS)`；函数注释写明为什么省掉在线后缀。验证：`npx vue-tsc --noEmit` 0 错误。

## 2. 断言

- [x] 2.1 改 `frontend/tests/shared/p0/device-address.spec.ts`：在线设备断言改为 `R5CT62RH88F · SM-S9010`，并新增「离线设备保留 `(OFFLINE)`」一条。验证：`npx vitest run tests/shared` 全绿。
- [x] 2.2 改 `frontend/tests/ai-assistant/p0/sop-run-form.spec.ts` 的下拉文案断言为 `192.168.35.57:39569 · SM-G9730`。验证：`npx vitest run tests/ai-assistant` 全绿（69 条）。

## 3. 门禁

- [x] 3.1 `npx prettier --check` 两个改动文件通过；`npx eslint src/shared/helpers` 无新增问题（仅 `sop-form.ts` 一条既有 warning）。
- [x] 3.2 `python run.py check` 记录的结论：本变更不涉及新增门禁项，前端相关项在后续 chore 变更中一并转绿。
