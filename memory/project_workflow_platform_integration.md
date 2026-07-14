# 工作流模块已并入平台前端

- 路径：`frontend/src/modules/workflow/`，路由 `/workflow`
- 资源库：左侧目录树可建 **目录 / 页面流 / 测试用例**；页面流本地持久化；新建用例可同步到用例设计
- 页面关联：经 axios 拉 `/elements/pages`+`items`，右键「刷新关联元素」
- 用例同步：积木「打开用例 / 同步到用例库」↔ `/cases/definitions`
- Demo 沙箱 `tests/workflow-demo` 仍可独立跑（:9998）
- 依赖：`@vue-flow/*`、`blockly`；Pinia id `wf-workflow` / `wf-testCase`
