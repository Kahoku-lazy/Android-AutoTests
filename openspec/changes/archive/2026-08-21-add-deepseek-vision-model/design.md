## Context

- deepseek 提供商内置模型列表有两处副本：`AgentDetail.vue` 的 `providers` 数组（配置页下拉）与 `helpers/model-config.ts`（看板便签模型选项）。两处需同改（历史重复，未做收敛重构）。
- 图片链路已全通：前端上传 → `images[{media_type,data}]` → `chat_views._build_user_blocks` 生成 AgentScope `DataBlock` → openai formatter 转 image_url；无需为视觉模型改任何后端/通道代码。

## Goals / Non-Goals

**Goals:**

- 配置页与看板模型下拉均出现 `deepseek-v4-flash-vision-exp`，可选可测。

**Non-Goals:**

- 不做模型列表去重/收敛重构；不加"视觉"标记 UI；不改后端与通道。

## Decisions

**D1：模型 ID 直接用官方 `deepseek-v4-flash-vision-exp`，不改 formatter。**
DeepSeek 视觉 API 为 OpenAI 兼容（image_url），沿用现有 `formatter: openai`；模型名以官方 API 文档为准。

**D2：两处列表同改、不加视觉标记。**
保持最小 diff；用户按名称识别模型即可。

## 模块防火墙自检

- 纯前端配置列表变更，无写库、无跨模块、无通道变更。✅

## Risks / Trade-offs

- [非视觉模型发送图片时 DeepSeek API 可能报错] → 属于用户配置选择，模型列表已可区分视觉/非视觉；本次不改发送侧逻辑。
