## Why

`python run.py check` 的前端项长期挂着几笔存量债，让「门禁全绿」失去信号：两个 `.vue` 超过 500 行红线（`ai-assistant/chat.vue` 505、`ops-console/model-configs.vue` 538），18 个 `src/**/*.{vue,js,css}` 与约 50 个 `.ts` 未经 prettier 格式化。这些不是新功能引入的，但每次改动都要人工判断「这条红是不是我造成的」。

## What Changes

- **拆超红线组件**：
  - `ai-assistant/chat.vue`：样式外置到 `chat.style.css`（`<style src="./chat.style.css" scoped>`），`.vue` 505 → 262 行。
  - `ops-console/model-configs.vue`：名称草稿行（多行聊天名 / 单行语音名、发现模型名、地址校验）抽到 `composables/useModelNameDraft.ts`，样式外置到 `model-configs.style.css`，`.vue` 538 → 425 行。模板与 `save()` 的绑定名不变（解构时按原名重命名），行为不动。
- **prettier 存量**：对 `src/**/*.{vue,js,css}`、`src/**/*.ts`、`tests/**/*.ts` 跑一次 `prettier --write`，让 `prettier` 与 `prettier-ts` 两个门禁从红转绿。
- **不再需要的两处**（已被并行改动修掉，本次只做验证）：
  - `AppSidebar.style.css` 的品牌图标圆角已改为 `var(--radius-lg)`，`lint:styles` 批 4 现已通过。
  - `tests/dashboard/p0/useDashboardStats.spec.ts` 单跑与全量跑均可通过（此前那次失败是 vitest 转换缓存引发的偶发）。
- 不改业务行为、不改接口、不改路由；不新增白名单（`utils/frontend-whitelist.json` 保持原样）。

## 关联文档

无独立需求编号。来源是本轮收尾时对「既有门禁要不要单独清一轮」的确认：需求方要求单开一个 chore 变更，不与功能变更混提。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。纯格式与文件拆分的重构，对外行为不变，故 `skip_specs: true`。

## Impact

- 前端：`frontend/src/modules/ai-assistant/chat.vue`（+ 新 `chat.style.css`）、`frontend/src/modules/ops-console/model-configs.vue`（+ 新 `model-configs.style.css`、`frontend/src/modules/ops-console/composables/useModelNameDraft.ts`），以及 prettier 覆盖到的 `src/**` 与 `tests/**` 里的格式差异。
- 测试：无新增用例；`tests/ops-console`、`tests/ai-assistant`、`tests/shared` 必须保持全绿以证明拆分无回归。
- 文档漂移风险：格式化会移动若干行号，`*.md` 里若按行号引用需要另行校对（本变更不改文档）。
