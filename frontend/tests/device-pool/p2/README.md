# [P2] 默认不写 Vitest

| 项 | 原因 | 去向 |
|----|------|------|
| DevicePoolView.vue 整页 mount | 多组件拼装，mock 多收益低 | E2E |
| 设备操作动画（animejs） | 视觉无业务分支 | 不测 |
| 真后端扫描/连接/心跳联调 | 依赖设备与网络 | E2E |

优先级约定见：`../../PRIORITY_TEMPLATE.md`
