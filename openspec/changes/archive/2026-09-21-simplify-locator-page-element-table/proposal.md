## Why

元素定位文件详情页（Android 页面叶子）当前是「左截图圈选 + 右元素表」分栏，工具栏还有「全部 / 可点击 / 有文本 / 测试点」分段筛选。定位资产应以表格浏览与编辑为主，截图圈选与前端筛选占用主工作区且与设备检查器职责重叠。本次去掉截图面板与筛选控件，让当前页以全宽表格呈现元素定位信息。

## What Changes

- 去掉页面元素工作台左侧 `.shot-pane` 截图圈选面板及其与表格的双向高亮联动。
- 去掉工具栏分段筛选「全部 / 可点击 / 有文本 / 测试点」；列表始终展示该页全部元素（仍受既有 `limit` 上限约束）。
- 工作台改为单一表格面：保留别名、文本、resource-id、XPath、坐标、测试点等列及行内编辑（别名、测试点开关）。
- 删除仅被该工作台引用的 `PageScreenshotOverlay.vue`。
- 后端 `GET /api/elements/pages/{id}/items/` 的 `filter` 查询参数与 `screenshot_path` 响应字段 **本次不删**（设备检查器导入快照仍写截图；其它调用方可继续按 filter 过滤）。前端固定按未筛选列表请求。

**BREAKING**：无 API 破坏。仅前端可观察布局与筛选控件消失。

## 关联文档

- 需求编号：`PRD-04-元素定位`

## Capabilities

### New Capabilities

- `element-locator-page-workbench`: 元素定位 Android 页面叶子的元素工作台布局与列表契约（全宽表格、无截图圈选、无分段筛选）。

### Modified Capabilities

（无。既有 `element-locator-projects` 只覆盖项目/目录树/叶子身份，不含该工作台 UI。`frontend-l0-design-tokens` 中 `el-radio-button` 场景仍由设备检查器「保存到元素」对话框等其它分段控件覆盖，不因本页去掉筛选而改需求。）

## Impact

- 前端：`frontend/src/modules/element-locator/components/PageElementsWorkbench.vue`；删除 `PageScreenshotOverlay.vue`；`apiPageItems` 调用改为固定未筛选（`all` 或省略 `filter`）。
- 后端 / 路由 / 数据模型 / 迁移：零改动。
- 设备检查器筛选栏与截图面板：不改。
- 测试范围：元素定位相关前端单测（若有覆盖该组件）、`npm run typecheck`、`vue-frontend-check` 针对改动文件。
- 恢复方式：`git revert`。
