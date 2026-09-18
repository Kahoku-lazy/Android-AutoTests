## 1. 死 prop 修复

- [x] 1.1 `element-locator/components/PageElementsWorkbench.vue` 的裸 `stripe` 改为 `:striped="true"`；验证：全仓行级检索 `^\s*stripe$` 命中数 **0**，同模块其余 4 处 `:striped` 未受影响
- [x] 1.2 Chromium 断言：`AppTable` 在 `:striped="true"` 下渲染斑马纹；验证：断言 PASS（见 §4.4）

## 2. 零引用组件删除

- [x] 2.1 删除 `modules/ai-assistant/components/AgentModelConfig.vue`（78 行，0 引用）；验证：文件不存在，构建通过
- [x] 2.2 删除 `modules/workflow/components/WorkflowFileBrowser.vue`（550 行，0 引用）；验证：文件不存在，构建通过

## 3. 移出范围（本轮实测确认，已在 proposal 登记）

- [x] 3.1 `report-generator/constants.ts` 的 17 个零引用导出清退 **移出本变更**：首次尝试因按 `;` 判定（项目不使用分号）而损毁文件，已 `git checkout --` 完整恢复（**29 导出 / 162 行，与 HEAD 一致**）；后续需按"下一个顶层导出/注释块起始"为界的安全策略重做
- [x] 3.2 令牌清退、死 CSS 规则清退、`dashboard`/`report-generator` 令牌文件化 —— 一并另开批次

## 4. 门禁与验收

- [x] 4.1 `npm run lint:styles` 退出码 0；验证：批 1/2/3 全绿
- [x] 4.2 `npx vite build --mode development` 通过；验证：记录退出码与耗时（删除文件与 prop 改动后必须通过）
- [x] 4.3 `npm run typecheck` 错误集合与改动前对比不新增；验证：逐文件对比错误分组
- [x] 4.4 编码安全：改动由 `edit` 工具与 `Remove-Item` 完成，无文本批量改写；验证：乱码扫描命中 0
- [x] 4.5 `git status` / `git diff --stat` 与 `proposal.md` 的 Impact 段一致；验证：仅 1 个文件修改 + 2 个文件删除