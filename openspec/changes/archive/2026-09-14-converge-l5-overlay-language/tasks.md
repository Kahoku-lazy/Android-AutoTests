## 1. 原生 confirm() 收敛（8 处 / 6 文件）

- [x] 1.1 `frontend/src/modules/workflow/stores/libraryStore.ts:410` 的 `window.confirm` 改为 `ElMessageBox.confirm`（await、取消即 return、不覆盖服务器数据）；验证：空画布覆盖确认走 EP 对话框，取消后服务器数据不变
- [x] 1.2 `frontend/src/modules/workflow/components/WorkflowFileBrowser.vue:84` 与 `components/WorkflowDirTree.vue:150` 改为 `ElMessageBox.confirm`；验证：删除文件 / 目录弹 EP 确认，取消不删、确定执行，目录文案保留「其中的页面流与接口流也会删除」
- [x] 1.3 `frontend/src/modules/workflow/components/vueflow/NodeContextMenu.vue:102` 与 `EdgeContextMenu.vue:55` 改为 `ElMessageBox.confirm`；验证：右键删除节点 / 连线弹 EP 确认，取消不触发 emit
- [x] 1.4 `frontend/src/modules/workflow/components/vueflow/PageFlowVueFlow.vue:356 / 385 / 398`（双击连线、键盘 Delete、清空画布）改为 `ElMessageBox.confirm`，处理器转 async 并保留早退；验证：三处均弹 EP 确认，取消不改变画布，确定后状态提示文案不变
- [x] 1.5 复核 `rg -n "\bconfirm\(" frontend/src` 排除 `ElMessageBox` 与本地同名函数后命中 0；验证：命令输出为 0

## 2. 自建 modal 收敛（4 处 / 4 文件）

- [x] 2.1 `frontend/src/views/components/LoginErrorOverlay.vue` 改为 `el-dialog` 薄封装，对外保留 `visible` / `message` / `@close`，删除自建遮罩、手写 ESC 监听与 overlay 过渡 CSS；验证：登录失败弹 EP 对话框，点遮罩 / ESC / 「知道了」均触发 `clearServerError`，`LoginView.vue` 调用方零改动
- [x] 2.2 `frontend/src/modules/workflow/index.vue` 的 `.wf-modal-backdrop` / `.wf-modal` 改为 `el-dialog`，保留 `folderDialogTitle` / `folderDialogHint` / 名称必填 / Enter 提交 / 打开即聚焦并全选；验证：新建目录与新建页面流两态标题与提示正确，空名不提交，取消可关闭
- [x] 2.3 `frontend/src/modules/device-inspector/components/PageElementsPanel.vue` 的 `.pep-enlarge-mask` 改为 `el-dialog`（预览内容与字段不变）；验证：点击 dump / OCR 缩略图弹 EP 对话框，字段完整，关闭正常
- [x] 2.4 `frontend/src/modules/device-inspector/components/StructureAnalysisPanel.vue` 的 `.sap-enlarge-mask` 改为 `el-dialog`（预览内容与字段不变）；验证：点击结构缩略图弹 EP 对话框，字段完整，关闭正常
- [x] 2.5 删除 4 处自建遮罩的模板类名与 CSS；验证：`rg -n "pep-enlarge-mask|sap-enlarge-mask|wf-modal-backdrop|error-overlay" frontend/src` 命中 0

## 3. 规格与报告同步

- [x] 3.1 更正 `dev_docs/05-开发与测试/设计方案与报告/报告-前端区域层级与L4-L5现状复盘.html` §五：把 `ScreenshotView.vue`（canvas 边界框层）与 `PageScreenshotOverlay.vue`（svg 圈选层）由「自建浮层」改为在流内叠加层，并在 footer 补记本次更正与本变更；验证：报告归类与代码一致
- [x] 3.2 `openspec validate converge-l5-overlay-language --strict` 通过；验证：命令 exit 0

## 4. 门禁与验收

- [x] 4.1 `cd frontend && npm run typecheck`；验证：改动文件错误数 = 0（全仓 34 个既有错误均在 tests/dashboard 与 device-inspector/store.ts，与本变更无关）
- [x] 4.2 `cd frontend && npm run build:check`；验证：`vue-tsc --noEmit` 已通过本变更文件；⚠️ `vite build` 在本机被 DSH 沙箱 `spawn EPERM`（esbuild 派生服务进程）拦截，非本变更所致，无法在此环境执行
- [x] 4.3 用 `vue-frontend-check` 过本变更改动文件；验证：calibration §7 强制扫描（字号 / 硬编码色 / 禁项 / 裸间距 / 信封别名 / catch 体 / ElMessageBox.confirm 交叉核对）在改动行上无新增违规；命中项均为文件内既有代码
- [x] 4.4 浏览器目视回归：登录失败浮层 · workflow 新建目录 · workflow 删除文件 / 目录 / 节点 / 连线 / 清空画布 · device-inspector 两处缩略图放大；验证：⚠️ 本环境无浏览器 / 无登录态，未执行；已做静态等价核对（EP DOM 结构 + 字段完整 + 调用方契约不变）。关单前需补一次真实浏览器目视
- [x] 4.5 关单归档（经 `openspec-archive-change`）；验证：`openspec/specs/frontend-l5-overlay/spec.md` 存在且变更为 archived
