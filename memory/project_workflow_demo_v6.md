---
name: workflow-demo V6 优化要点
description: ComfyUI 页面流 + Scratch 用例双 Tab、图→用例桥、保存 key、导出 flat_steps
type: project
---

# workflow-demo V6

- 路径：`tests/workflow-demo`（Vue3+Vite+Pinia+自研 SVG），`npm run dev` → :9998
- 双 Tab：页面流（workflowStore）↔ 用例（testCaseStore）；`bridgedElements` 打通 xpath
- 用例保存必须同时写 `tc_tree_current` 与 `tc_tree_{name}`，否则按名加载失败
- 导出 `testcase-scratch-v1` 含可编辑 `package_name` + `blocks` + `flat_steps`（对齐 TestStep）
- 积木参数优先在选中块内联编辑；侧栏为高级参数 +「从页面流选元素」
- 连线命中：贝塞尔多点采样；端口 hover 有 ring+tooltip；双击标题重命名
