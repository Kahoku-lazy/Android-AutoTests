## 1. 纯逻辑（可脱离 DOM 测）

- [x] 1.1 新建 `frontend/src/modules/ai-assistant/helpers/case-picker.ts`：`CaseRow` / `CaseProjectGroup` 输入类型与 `filterCaseProjects(projects, query)`（同时匹配 `title` 与 `id`，忽略大小写与首尾空白，只返回含命中行的分组）、`countHitCases(groups)`、`pickableIds(groups)`。验证：`tests/ai-assistant/p0/case-picker.spec.ts` 5 条过滤/分组断言全绿。
- [x] 1.2 同文件补 `hitbarText({inScope, elsewhere, projectName})` 与 `summarizePicked(selected, projects)`（条数、覆盖项目数、前 4 条名称、剩余条数）。验证：三种提示形态（都有命中 / 项目内零命中 / 无其他命中）+ 摘要截断各 1 条断言。
- [x] 1.3 同文件补 `toggleAll(selected, ids)` 与 `findCase(projects, id)`：全选中则整体移除，否则只补未选项，且不改动入参。验证：3 条断言（含「空编号返回新数组」）。
- [x] 1.4 备注：`normalizeQuery` / `matchesCase` 从 1.1 一并落地，供上面三个函数复用，未单列。

## 2. 选择器组件

- [x] 2.1 新建 `frontend/src/modules/ai-assistant/components/CasePicker.vue`（214 行 `<500`）：项目栏（全部项目 + 各项目 + 条数，命中为 0 时禁用）、`type="search"` 搜索框、分组列表（段头：项目名 / 条数 / 全选本项目；行：复选 + 标题 + 编号徽标）、面板头「已选 N 条」、提示条、清空。`props`：`projects` / `modelValue` / `loading` / `error`；`emits`：`update:modelValue` / `retry`。验证：`npx vue-tsc --noEmit` 0 错误。
- [x] 2.2 三态接共享件：`SkeletonCard variant="list"` / `ErrorState`（可重试）/ 两种 `EmptyState`（没有项目、没有匹配）；加载分支排在空态之前，不会先渲染假空态。验证：`sop-run-form.spec.ts` 的「切来源」「摘要」用例走通了空/有数据两条分支。
- [x] 2.3 样式按方案稿落地：实线描边、`--app-space-*` 间距、`--app-size-*` 字号、`--c-case` 18% 浅底做选中态；`rail` 与 `list` 各自 `max-height: 320px; overflow-y: auto`，弹窗本体不滚。验证：`node tests/check-style-gates.mjs` 批 1/2/3 通过、批 4 仅剩 1 处既有违规（见 4.4）；`check-dashed-whitelist.mjs` 0 处虚线。
- [x] 2.4 拆分：组件样式外置到 `CasePicker.style.css`（326 行），`<style src="./CasePicker.style.css" scoped>` 引入，`.vue` 由 540 行降到 214 行（门禁 `vue-file-size` 要求 <500）。

## 3. 运行弹窗改版

- [x] 3.1 改 `SopRunForm.vue` 为两栏：左列「用例来源」分段控件 + 设备下拉 + 已选摘要卡；右列 `<CasePicker>` 或 YAML 面板；`@media (max-width: 1023px)` 回退单列。验证：`vue-tsc` 通过、`vite build` 36s 成功。
- [x] 3.2 footer 改由 `sopRunError()` 驱动：缺项时按钮禁用并在左侧显示该文案，齐备时显示「已选 N 条用例 · 可以开始」。验证：单测断言三种缺项文案与 `disabled` 属性；`canRun` 同时拦截设备列表加载失败。
- [x] 3.3 保留既有口径：切来源清空另一侧输入、工作流名只读展示（「工作流：<名>」）、提交成功仍 emit `submitted`。验证：`sop-run-form.spec.ts` 12 条全绿，含「切换来源清空已选」「平台来源只带用例编号」。
- [x] 3.4 改 `SopWorkflowSection.vue` 运行弹窗宽度为 `min(960px, 92vw)`，未新增 `append-to-body`；同步更新文件头注释（运行输入已含平台用例）。验证：弹窗仍在 `.ai-assistant-page` 内，`assistant-field` / `assistant-input` 皮肤生效。
- [x] 3.5 样式外置到 `SopRunForm.style.css`（226 行），`.vue` 239 行，给后续改动留出体积余量。

## 4. 测试与门禁

- [x] 4.1 新增 `frontend/tests/ai-assistant/p0/case-picker.spec.ts`（14 条）：按编号搜索、按名称片段搜索（小写）、零命中、可勾选编号顺序、整体切换三段、三种提示文案、摘要条数/项目数/折叠。验证：`npx vitest run tests/ai-assistant` → 69 passed。
- [x] 4.2 改 `frontend/tests/ai-assistant/p0/sop-run-form.spec.ts`（12 条）：设备断言收窄到 `.sop-run__side input[type="text"]`；新增「按钮禁用 + 写明缺项」「选用例+设备后可用」「摘要跨项目汇总」「切来源清空已选」「来源是两段控件」「平台来源只带用例编号」。验证：同上 69 passed。
- [x] 4.3 门禁（本变更范围）：`npx vitest run tests/ai-assistant` 69/69、`npx vue-tsc --noEmit` 0 错误、`npx vite build` 成功、`npx prettier --check`（7 个改动文件）通过、`node tests/check-dashed-whitelist.mjs` 通过、`gen_arch_stats.py --check-frontend` 无新增超标。
- [x] 4.4 门禁（仓库级）`python run.py check`：**13/25 通过，12 项失败，全部为本次变更之前既有**，证据如下——`vitest` 仅 `tests/dashboard/p0/useDashboardStats.spec.ts` 失败（期望对象缺 `byModel` / `voiceByModel`，与本次无关）；`vue-file-size` 超标的 2 个文件为 `ops-console/model-configs.vue`（538 行）与 `ai-assistant/chat.vue`（505 行）；`prettier` / `prettier-ts` 命中的是既有未格式化文件（如 `api/assistants.ts`、`chat.vue`）；`lint:styles` 唯一失败项是 `shared/components/AppSidebar.style.css:209 border-radius: 8px`（该行在 HEAD 中已存在，本次 diff 未触碰该文件）；`ruff` / `openapi` / `pytest-collect` / `engines-*` 属后端与引擎面，本次未改动。
- [x] 4.5 模块自检：新增虚线 0 处（`dashed-whitelist` 通过）；字号/间距/颜色全部走令牌；新 `.vue` 214 / 239 行；共享件只用 `DoodleBtn` / `EmptyState` / `ErrorState` / `SkeletonCard`，未自建第二套。
