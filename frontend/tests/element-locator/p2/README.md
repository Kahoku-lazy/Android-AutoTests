# [P2] 默认不写 Vitest

| 项 | 原因 | 去向 |
|----|------|------|
| ElementManager.vue 整页 mount | 多组件拼装 + 长按拖拽动画，mock 多收益低 | E2E |
| 三树同构重构（useElementTree / useWebGroupTree / useApiGroupTree） | 复制粘贴式同构已用共享测试夹具覆盖，重构源码明确不做 | 不做 |
| 真后端页面/元素联调 | 依赖设备与网络 | E2E |

优先级约定见：`../../PRIORITY_TEMPLATE.md`
