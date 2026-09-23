## 1. 错误信息接入

- [x] 1.1 `frontend/src/modules/ai-assistant/composables/useToolDebug.ts`：schema 加载失败与 invoke 失败改用 `formatApiError`（自 `@/shared/api-client` 导入），`buildParams` 的本地校验错误保持原样，验证：`cd frontend && npm run typecheck` 通过

## 2. 用例

- [x] 2.1 `frontend/tests/ai-assistant/p0/useToolDebug.spec.ts` 增加用例：invoke 拒绝且响应体带 `message` → 断言 `invokeError` 与 `ElMessage.error` 展示该 message 而非状态码原文；另断言缺必填参数仍提示「请填写必填参数」，验证：`cd frontend && npx vitest run tests/ai-assistant/p0/useToolDebug.spec.ts` 通过

## 3. 门禁

- [x] 3.1 前端门禁：`npm run lint:styles`、`npm run typecheck`、`npx vitest run tests/ai-assistant`，验证：全部通过，无新增 vue-tsc 错误
