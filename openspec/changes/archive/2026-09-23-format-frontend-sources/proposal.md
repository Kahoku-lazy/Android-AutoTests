## Why

前端源码从未按仓库既有的 prettier 配置格式化过：`.vue/.js/.css` 有 **110 个文件**、`.ts` 有 **98 个文件**不合规（合计约 208 个文件，占前端源码的多数）。这使两道格式门禁长期为红——`prettier`（阻塞项）直接失败、`.ts` 覆盖（告警项）失败，也让后续任何改动的 diff 混入无关格式噪音。

## What Changes

- 用仓库既有配置（`frontend/.prettierrc`）对 `frontend/src/**/*.{vue,js,css,ts}` 执行一次全量格式化，文件内容与配置均不改动其他任何规则。
- 不手工调整任何代码语义；本次改动按定义只含空白、换行、引号、尾随逗号等格式差异。
- **BREAKING**：无。

## 关联文档

无对应需求编号（未关联 PRD / ARCH）。本变更为格式债务清理，需求来源为门禁实跑发现的格式红灯，已在 proposal 内完整描述。

## Capabilities

### New Capabilities

无。纯格式整理，不改变系统行为，按 schema 约定置 `skip_specs: true`。

### Modified Capabilities

无。

## Impact

- 仅影响 `frontend/src/` 下的 `.vue/.js/.css/.ts` 文件，约 208 个；不涉及后端、API 契约、数据模型或依赖。
- 预期结果：`prettier --check` 在 `{vue,js,css}` 与 `.ts` 两个范围上均为 0 不合规 → 阻塞项 `prettier` 转 PASS，告警项 `prettier-ts` 转 PASS。
- 代价：本次 diff 较大且全为格式差异，会掩盖同期的语义改动。缓解：本变更单独成提交，不与任何语义改动混合；审计时可对非空白差异单独核验。
