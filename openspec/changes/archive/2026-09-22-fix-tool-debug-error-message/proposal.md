## Why

调试页捕获 API 错误时只取 axios 的 `e.message`，于是界面显示 `Request failed with status code 400`，而服务端其实已经在错误信封里给了可读的 `message`（`EnvelopeJSONRenderer` 对 4xx/5xx 输出 `{status:false,message}`）。项目通用件 `formatApiError`（`shared/types/api-error.ts`，经 `shared/api-client` re-export）已在 9 个模块使用，只有 ai-assistant 走裸 `e.message`——排障时真实原因不可见。

## What Changes

- `composables/useToolDebug.ts` 的两处**API 错误**改用 `formatApiError`：schema 加载失败（`error`）与 invoke 失败（`invokeError` 及其 ElMessage）。
- **本地参数校验错误保持原样**：`buildParams` 抛的是本地 `Error`（如「请填写必填参数：serial」），MUST NOT 交给 `formatApiError`——那会把可读的本地提示替换成「网络连接失败，请稍后重试」。
- **不**改服务端状态码（由 `fix-tool-invoke-error-status` 承接）；**不**扫同模块其余同类泛化兜底（见 Impact）。

## 关联文档

- PRD-00（需求总纲，AI 工具箱增量）
- 前置变更：`add-platform-tool-debug`、`fix-tool-invoke-error-status`（服务端按成因给状态码）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-platform-tool-debug`: 新增「调试失败展示服务端可读错误」要求——加载/执行失败时展示服务端 `message`，MUST NOT 只显示 HTTP 状态码原文；本地参数校验提示 MUST 保持其本身文案。

## Impact

- 前端：`frontend/src/modules/ai-assistant/composables/useToolDebug.ts`
- 测试：`frontend/tests/ai-assistant/p0/useToolDebug.spec.ts`
- **已知同类问题（本单明确不扫）**：同模块 `useToolbox.ts`（`'删除失败'`/`'上传失败'`/`'操作失败'`）、`usePlatformTools.ts` 与 `usePlatformConfig.ts`（`'操作失败'`）、`KnowledgeBase.vue`（`'操作失败'`）、`useToolbox.loadItems`（仅 `console.error`）。这些仍会丢失服务端 message，属独立清扫。
- 后端 / 迁移 / 依赖：无
