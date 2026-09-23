## Context

见 `proposal.md` - Why。现状：`AgentRouteCard.vue` 用 `DoodleNote` 的 `#header` 居中渲染 `label`（入口传入「控制设备」），`#default` 为 48×48 头像 + 名称 + 连通徽标两行，`#actions` 已是「校验」「配置」。连通三态逻辑（`routeConnState` / `badgeClass` / 文案）已稳定，本设计只改信息架构与布局。入口 `index.vue` 的 `routeCards` 目前带 `label: '控制设备'`。

## Goals / Non-Goals

**Goals:**

- 去掉 header 槽；身份区改为头像 + 三行；职责对 `device_control` 写死「职责：UI自动化」。
- 头像正方形，边长跟三行自然高度走（`align-items: stretch` + `aspect-ratio: 1`），不再写死 48px。
- 底部操作槽不变。

**Non-Goals:**

- 不改探测、health 字段、配置弹层、后端。
- 不改 `DoodleNote` / `DoodleBtn` 共享 API。
- 不引入第二张线路卡；职责映射只覆盖当前唯一的 `device_control`。

## Decisions

- **职责文案放组件常量，不走后端**：看板目前只有控制设备一条线路，用户指定职责为「UI自动化」。备选把 `label` 继续当标题并另加职责字段——会与「去掉功能标题带」冲突，否决。入口可删 `label` prop，或把 prop 改名为 `duty` 且值为「UI自动化」；实现时选更少 diff 的一种。
- **头像高度跟文字走，而不是把文字压成 48px**：用户要求三行与头像宽度一致；头像是正方形，故边长 = 三行总高。备选固定大头像（如 72px）再让文字垂直居中——三行增高后会对不齐，否决。
- **状态行保留现有徽标样式**：第三行仍用 `.route-conn-badge` 与三色 token，不改文案。长文案允许在文本列内换行（`white-space: normal`），避免撑破卡片。
- **名称过长省略**：第一行继续 `ellipsis` + `nowrap`。

## 模块防火墙自检

- 跨 App import：不涉及后端。
- 跨 App service/runner：不涉及。
- 写库收敛到 api.py：无写库。
- 前端不直连数据库：仅改卡片 DOM 与样式。

## Risks / Trade-offs

- [emoji 头像在大正方形里显得空] → 字号随头像边长用令牌档位（`--app-size-xl` 或更大一档），不硬编码 px 色值。
- [三行增高后卡片变高] → 网格 `align-items: start` 已存在，不强制等高。
- [像素级「宽度=高度」单测脆弱] → 规格允许 1px 舍入；单测优先断言 DOM 结构与文案，布局用 CSS 合同（`aspect-ratio: 1` + stretch）保证，不必上浏览器量像素。
