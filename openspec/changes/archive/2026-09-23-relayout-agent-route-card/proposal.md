## Why

智能体看板线路卡（`AgentRouteCard`）当前把功能名放在独立标题带，身份区只有头像、名称与连通徽标两行，职责不显性，且头像固定 48px，与右侧文案不对齐。需要改成「左头像、右三行（名称 / 职责 / 助手状态）、底校验与配置」的身份卡，让一眼能读出谁在值班、做什么、能不能用。

## What Changes

- 去掉线路卡顶部独立功能标题（现「控制设备」header）
- 身份区改为横向：左侧正方形头像；右侧三行与头像等高（边长等于三行自然高度）
  - 第一行：助手名称（`route_configs.device_control.name`，缺省回落智能体名）
  - 第二行：职责文案，控制设备线路固定为「职责：UI自动化」
  - 第三行：助手状态（沿用既有三态 + 校验中过程态文案）
- 底部保留「校验」「配置」按键（超管可见），行为不变
- 单测覆盖三行结构与职责文案；连通三态断言保持

## 关联文档

- PRD-08（AI 助手 · 智能体看板线路展示）
- 说明：本次只改看板卡片信息架构与布局，不改探测协议与接口契约

## Capabilities

### New Capabilities

- `ai-assistant/route-card-identity`：看板线路卡身份区布局与三行信息（名称 / 职责 / 状态）及底部操作区

### Modified Capabilities

（无。连通三态文案与探测语义仍由 `ai-route-connectivity` 约束，本变更不改那些需求。）

## Impact

- 前端：`frontend/src/modules/ai-assistant/components/AgentRouteCard.vue`；`index.vue` 若仍向卡片传 `label` 则改为职责映射或删除无用 header
- 模块说明：`frontend/src/modules/ai-assistant/AGENTS.md` 看板卡片信息架构
- 测试：`frontend/tests/ai-assistant/p0/AgentRouteCard.spec.ts`
- 不影响：后端 API、health 探测、配置弹层、`DoodleNote` / `DoodleBtn` 共享件 API
