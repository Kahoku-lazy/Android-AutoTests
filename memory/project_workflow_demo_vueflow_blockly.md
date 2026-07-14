---
name: workflow-demo Vue Flow / Blockly 体验选型
description: 四 Tab 对比：Vue Flow 页面流、Blockly 用例、自研 SVG 对照；选型后再引入平台
type: project
---

# workflow-demo 库体验层

- 依赖：`@vue-flow/core` + background/controls/minimap、`blockly`
- 默认 Tab：`页面流 · Vue Flow` / `用例 · Blockly`；后两个为自研 SVG 对照
- Vue Flow 与自研共用 `workflowStore`（bridgedElements / 端口类型校验）
- Blockly 双向同步 `testCaseStore`；支持撤销、缩放、toolbox、定位/包名/超时字段
- 启动：`cd tests/workflow-demo && npm run dev` → :9998
- 选型注意：产物 JS ~1.1MB（主要 Blockly）；引入平台需考虑按路由懒加载
