# [P2] 默认不写 Vitest

| 项 | 原因 | 去向 |
|----|------|------|
| index.vue（测试运行器整页，即 TestRunnerView）mount | WS 消息 + 队列轮询 + 防抖保存三链路叠加，全量 mock 拼装成本高、收益低 | E2E |
| 真实 WebSocket 连接与断线重连 | 依赖真后端 WS 推送与真实网络抖动；P0/P1 已用 FakeWebSocket 覆盖逻辑层（seq gap / 退避重连 / 注入） | E2E |
| 真后端任务联调（创建→启动→排队→执行→停止/删除） | 依赖设备与后端，P0/P1 已 mock 覆盖编排与三分支 | E2E |

优先级约定见：`../../PRIORITY_TEMPLATE.md`
