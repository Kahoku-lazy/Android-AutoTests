## 1. ai-assistant（2 处）

- [x] 1.1 `components/AgentBasicInfo.vue`：删除 `.avatar-row` 的 `--avatar-shadow: 0 2px 8px rgba(61, 52, 40, 0.08)`，`.avatar-preview` 改用 `var(--app-shadow-sm)`；验证：全仓检索 `--avatar-shadow` 命中数 0，该文件不再有裸 `rgba()`
- [x] 1.2 `components/AgentFormFooter.vue`：`.nav-save:hover` 的 `0 4px 14px var(--nav-save-glow)` 改为 `var(--app-shadow-lg)`，并删除零消费方的 `--nav-save-glow` 与注释中的"hover 光晕"字样；验证：全仓检索 `--nav-save-glow` 命中数 0；Chromium 实测 hover 阴影为 `rgba(0,0,0,0.06) 3px 4px 0px 0px`（blur 0），`translateY(-2px)` 反馈保留

## 2. device-inspector（4 处）

- [x] 2.1 `components/ScreenshotView.css` 的 `.screenshot-panel::before` 图钉影改为 `1px 2px 0 0 var(--screenshot-pin-shadow-color)`；验证：Chromium 对伪元素实测 `rgba(0,0,0,0.1) 1px 2px 0px 0px`（blur 0）
- [x] 2.2 `components/ScreenshotView.css` 的 `.screen-img` 改为 `4px 4px 0 0 var(--screenshot-img-shadow-color)`；验证：实测 `rgba(0,0,0,0.1) 4px 4px 0px 0px`（blur 0）
- [x] 2.3 `components/PageElementsPanel.vue` 的 `.pep-enlarge` 改为 `4px 4px 0 0 var(--pep-enlarge-shadow-color)`；验证：实测 `rgba(0,0,0,0.3) 4px 4px 0px 0px`（blur 0），3px 墨色描边保留
- [x] 2.4 `components/StructureAnalysisPanel.vue` 的 `.sap-enlarge` 改为 `4px 4px 0 0 var(--sap-enlarge-shadow-color)`；验证：实测与 `.pep-enlarge` 规格一致（同为 `rgba(0,0,0,0.3) 4px 4px 0px 0px`）

## 3. workflow（2 处）

- [x] 3.1 `components/vueflow/PageFlowNode.vue`：`.pf-node.api` 的外发光改为 `var(--app-shadow-md)`，删除零消费方的 `--wf-node-api-glow`；验证：全仓检索 `--wf-node-api-glow` 命中数 0；实测 `rgba(0,0,0,0.05) 2px 3px 0px 0px`（blur 0），左侧色条强调保留
- [x] 3.2 `components/vueflow/PageFlowVueFlow.vue` 的元素选择浮层改为 `4px 4px 0 0 var(--wf-picker-shadow)`；验证：实测 `rgba(74,78,105,0.1) 4px 4px 0px 0px`（blur 0）；`border-radius: 14px` 按计划未改（属变更 10）

## 4. 规格与门禁

- [x] 4.1 新增「阴影规格扁平且不含模糊投影」要求（delta 于 `specs/frontend-l0-design-tokens/spec.md`）；验证：`openspec validate enforce-flat-shadow --strict` 通过，归档后已合入 main spec
- [x] 4.2 复扫复核：直接声明扫描命中 **0**、`--*shadow*` 自定义属性扫描命中 **0**；验证：两份扫描输出均为 0
- [x] 4.3 spread 环未受影响：`PageFlowNode.vue` 的 `0 0 0 3px` / `0 0 0 1px` / `0 0 0 4px` 三处与改动前一致；验证：检索结果仍为 3 处
- [x] 4.4 `npm run lint:styles` 退出码 0，批 1/2/3 全绿；验证："消费位置裸色字面量"仍为 **33 处** —— 该 gate 只统计**消费位**字面量，而 `--avatar-shadow` 是**自定义属性声明**、被其显式跳过（源码 `consumptionLiterals` 对 `--x:` 开头跳过），故计数不变属预期；裸值的消除改由 `--avatar-shadow` 检索命中 0 与浏览器断言共同证明
- [x] 4.5 `npx vite build --mode development` 通过（`built in 41.92s`，退出码 0）；验证：既有 `tests/dashboard/**` / `device-inspector/store.ts` / `case-manager/ProjectTree.vue` 无关报错未新增（本变更未触碰任何 `.ts` 与这两个文件）
- [x] 4.6 Playwright + Chromium 渲染断言（真实 `tokens.css` + `style.css` + `workbench-theme.css` + `ScreenshotView.css` + 6 个组件的全部 `<style>` 块与复刻 DOM）：**17 项断言全 PASS**；含**解析器有效性对照** —— 已知模糊写法 `0 8px 32px` 被正确解析为 blur=32，而 8 个收敛点实测 blur 均为 **0** 且阴影非 `none`（证明令牌解析成功、浮层未失去层次）。**限制**：契约级验证，未加载真实运行中的应用与数据
- [x] 4.7 `git diff --stat` 本变更部分为 7 个文件：`AgentBasicInfo.vue` / `AgentFormFooter.vue` / `ScreenshotView.css` / `PageElementsPanel.vue` / `StructureAnalysisPanel.vue` / `PageFlowNode.vue` / `PageFlowVueFlow.vue`，与 `proposal.md` 的 Impact 段一致；工作区其余改动属变更 1/2 与其他在飞工作，未触碰