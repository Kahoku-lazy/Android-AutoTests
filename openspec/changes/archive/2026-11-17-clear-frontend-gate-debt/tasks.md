## 1. 拆超标组件

- [x] 1.1 `ai-assistant/chat.vue`：`<style scoped>` 外置为 `chat.style.css`（242 行），组件改 `<style src="./chat.style.css" scoped></style>`；`.vue` 270 行。验证：`gen_arch_stats.py --check-frontend` 不再点名。
- [x] 1.2 `ops-console/composables/useModelNameDraft.ts`（121 行）：抽出名称草稿行（`rows` / `loading` / `hint` / `single` / `reset` / `add` / `remove` / `names` / `validUrl` / `discover`）与「切到非聊天类型只留第一行」的 watch。验证：`npx vue-tsc --noEmit` 0 错误。
- [x] 1.3 `ops-console/model-configs.vue`：改用该组合式并**按原名解构**（`nameRows` / `loadingNames` / `discoverHint` / `singleModelName` / `addNameRow` / `removeNameRow` / `resetNameRows` / `namesInForm` / `validApiUrl` / `loadNames`），模板与 `save()` 零改动；删掉本地 `NameRow` 接口与 6 个辅助函数、清掉不再使用的 `discoverModelNames` import；内联样式外置为 `model-configs.style.css`（37 行），`.vue` 441 行。验证：`npx vitest run tests/ops-console` 31/31。
- [x] 1.4 `vue-tsc` 0 错误；`npx eslint src/modules/ops-console src/modules/ai-assistant` 0 error（仅 `sop-form.ts` 一条既存 warning）。

## 2. 格式存量

- [x] 2.1 `npx prettier --write "src/**/*.{vue,js,css}" "src/**/*.ts" "tests/**/*.ts"`：78 个文件被格式化。验证：`npx prettier --check` 两组 glob 均返回「All matched files use Prettier code style!」。
- [x] 2.2 格式化后全量复跑：`npx vitest run` → 78 files / 452 tests 全绿（格式化未破坏模板选择器）。

## 3. 复核既有两项

- [x] 3.1 `AppSidebar.style.css` 品牌图标圆角已是 `var(--radius-lg)`（并行改动）：`node tests/check-style-gates.mjs` 批 4 通过，`lint:styles` 整体转绿。
- [x] 3.2 `tests/dashboard/p0/useDashboardStats.spec.ts`：单跑 15/15、全量跑 452/452 均通过；此前那次失败是 vitest 转换缓存造成的偶发，无需改代码。

## 4. 门禁

- [x] 4.1 `npx vitest run` 452/452、`npx vue-tsc --noEmit` 0、`npx vite build` 成功。
- [x] 4.2 `python run.py check`：由 13/25 → **17/25**。本次负责的前端项全部转绿——`vitest`、`vite-build`、`prettier`、`prettier-ts`、`eslint`、`dashed-whitelist`、`vue-tsc`、`vue-file-size`、`inline-style`（`lint:styles` 由 `python run.py check` 之外单独跑，批 1/2/3/4 全通过）。
  剩余 8 项全部在后端与 engines，不在本 chore 范围，已记录：
  - `ruff-format` / `ruff-lint`：49 条（18 条 unsorted imports、**17 条 undefined-name**、7 条 unused import、6 条 print、1 条转义引号）。
  - `ruff-engines-format` / `ruff-engines-lint`：engines 侧同类问题。
  - `pytest-collect`：10 个用例文件收集失败（`tests/task/api/test_task_media*.py`、`test_task_stats.py`、`tests/task/unit/test_task_drain.py` 等），收集到 886 条。
  - `openapi-schema` / `openapi-coverage`：契约基线漂移与未文档化路径。
  - `engines-agents-retirement`：退役面残留检查。
