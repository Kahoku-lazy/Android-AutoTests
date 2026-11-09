## Why

「AI 用量」右侧的 Agent-01 / Agent-02 卡片现在是 Doodle 钉板卡：硬阴影 + 微倾 + 图钉，和同一区块左侧的统计卡（已改同色实线）视觉语言不一致，两列像拼在一起的两套卡。需求方给了「CARDS AS PARTS」参考（顶边色条 + 右上角黄圆 + 编号 + 细线无阴影），要求 Agent 费用卡按此风格重做。

## What Changes

- Agent 用量卡改为「零件卡」：
  - 2px 墨线描边、2px 圆角、**无阴影、无微倾、无图钉**；
  - 顶边 6px 模块色色条（按序号轮转 `--c-ai / --c-case / --c-runner / --c-workflow`）；
  - 右上角 52px 黄色四分之一圆（`--c-dashboard`，墨线描边）；
  - 左上角编号 `01 / 02`（与色条同色），标题 18px/800，四项数据保持两列。
- 数据、字段、排序、右列布局不变。

## 关联文档

- 参考图：用户提供的「CARDS AS PARTS」卡片族。
- 本变更只改 `dashboard` 模块内该类卡的皮肤，不动共享 `AppCard`。

## Capabilities

### New Capabilities

无（纯视觉变更，`dashboard-ai-usage` 已规定卡片内容与位置，本次不改契约）。

### Modified Capabilities

无。

## Impact

- 前端：`modules/dashboard/index.vue`（模板加编号与色条变量、scoped 样式重写 `.agent-usage-card`）。
- 后端 / 接口：无改动。
