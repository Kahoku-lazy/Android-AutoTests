## Context

现状（见 proposal.md - Why）：头像在三处流转——`AgentDetail.vue` 用 `FileReader` 把图片转 data URI 调 `POST /api/ai/upload-avatar/` 落库，`AgentBasicInfo.vue` 提供「上传图片」按钮与 emoji/外链输入，`AgentRouteCard.vue` 按 `data:image/` 前缀决定渲染图片还是 emoji。本次把这条链路整体收敛成「一枚内置图标」。`route-card-identity` 已约束「头像边长 = 右侧三行高度」，本次不动这条尺寸规则。

## Goals / Non-Goals

- Goals：头像视觉固定、上传入口消失、上传接口下线；「头像边长 = 三行高度」的布局约束保持不变。
- Non-Goals：不删数据库字段、不做数据迁移、不改任务列表与执行链路、不做深浅色两套图标。

## Decisions

1. **图标放 `frontend/public/agent-avatar.svg`，用常量路径引用**
   - 备选 A：塞进 `shared/icons/index.ts` 的 `makeIcon`——该工厂只吃单段 `d` + 单色 `currentColor`，而本图是 4 色 + `mask`，排除。
   - 备选 B：`shared/components/AgentAvatar.vue` 内联组件——会多出一个组件并让几何散在组件里，当前只有两处消费，性价比低。
   - 备选 C：`src/assets` 导入——可行，但 `frontend/AGENTS.md` 明确静态资源走 `public/`，按既有口径落。
   - 结论：`public/agent-avatar.svg` + `constants.ts` 里的 `AGENT_AVATAR_SRC = "/agent-avatar.svg"`（Vite 未配置 `base`，根路径可用）。

2. **卡片头像改为固定 `<img>`，容器去掉「图片相框」样式**
   - 现容器有 `border: 3px solid var(--ink)` + 暖白底 + emoji 字号；图标自带 8px 深蓝描边，再套 3px 边框会双重描边。
   - 保留 `ResizeObserver` 的「边长 = 三行高度」测量与硬阴影，尺寸规则不变。

3. **配置页保留只读预览**
   - 直接删掉整个「头像」项会让使用者以为功能丢失；保留 64px 预览 + 「系统内置头像，不可修改」一行，成本极低。

4. **后端只删接口，保留字段**
   - `AIAgent.avatar` / `route_configs.{route}.avatar` 保留，避免 migration 与历史数据风险；前端不再读写后它退化为遗留字段，后续可单开变更清理。

5. **保存请求不再带 `avatar`**
   - `AgentSerializer.avatar` 是 `required=False`，省略即保持库里原值，向后兼容，不需要后端配合。

## Risks / Trade-offs

- [历史 data URI 仍占行体积] → 本次不清理，只保证不再渲染；后续可单开「清空 avatar 列」的数据清理变更。
- [`agentAvatar` prop 删除可能牵动其它调用方] → 已确认仅 `index.vue` 一处传入，改动同批提交。
- [卡片视觉变重：SVG 自带描边 + 卡片硬阴影叠加] → 实现后在 312px 卡片上实机核对，必要时去掉头像容器阴影。
- [旧前端仍调用上传接口] → 接口删除后返回 404 而非 5xx，影响面仅限该按钮，随前端同批发布即可。

## Migration Plan

无数据迁移。部署顺序不敏感：先发后端只会让旧前端的上传按钮报 404；先发前端则上传入口先消失，后端接口成死代码。回滚只需还原前端与 `urls.py`。

## Open Questions

无。
