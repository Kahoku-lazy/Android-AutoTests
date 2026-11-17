## 1. 侧栏入口

- [x] 1.1 `frontend/src/shared/components/sidebarNavConfig.ts`：`ai` 分组 `label` 置空、入口文案改为「平台助手」。验证：`npx vitest run tests/shared/p0/sidebarNavConfig.spec.ts` 断言 `label === ""` 且 `items === ["平台助手"]`。
- [x] 1.2 `frontend/tests/shared/p0/sidebarNavConfig.spec.ts`：AI 分组期望改为空 label + 「平台助手」；AI任务分组去掉早已不存在的「测试报告」期望（`/reports` 未在 `router.ts` 注册）。验证：该文件 11 passed。

## 2. 页面命名

- [x] 2.1 `frontend/src/modules/ai-assistant/index.vue`：`WorkbenchHeader` 标题改为「平台助手」。验证：dev server HMR 后页头显示「平台助手」。
- [x] 2.2 `frontend/src/modules/ai-assistant/routes.ts`：`meta.title` 改为「平台助手」，浏览器标签页与页头一致。验证：`vue-tsc --noEmit` 通过。

## 3. 区块标题条

- [x] 3.1 新增 `frontend/src/modules/ai-assistant/components/SectionBar.vue`：`title` + `count` 两个 prop、`action` 插槽、弹性空白把动作推右；样式整段沿用原 `.sop-section__bar` 的取值（标题 20px / heavy / 墨色，计数 14px 次要色，gap 8px）。验证：`npx vue-tsc --noEmit` 通过。
- [x] 3.2 `frontend/src/modules/ai-assistant/index.vue`：助手区改用 `SectionBar`，标题「AI 助手」、计数「共 N 位助手」、动作为「新建助手」；删掉 `.ai-assistant-page__bar` / `__count` 两条样式。验证：`npx vitest run tests/ai-assistant` 全绿。
- [x] 3.3 `frontend/src/modules/ai-assistant/components/SopWorkflowSection.vue`：工作流区同样改用 `SectionBar`，删掉 `.sop-section__bar/__title/__count/__spacer` 四条样式。验证：同上；两区由同一组件渲染，几何一致。

## 4. 门禁

- [x] 4.1 `npx vitest run tests/shared/p0/sidebarNavConfig.spec.ts tests/ai-assistant` → **12 files / 60 tests passed**；`npx vue-tsc --noEmit` 退出码 0。
- [ ] 4.2 `python run.py check` 全绿：仍被仓库既有 12 项失败挡住（与本次无关）。
