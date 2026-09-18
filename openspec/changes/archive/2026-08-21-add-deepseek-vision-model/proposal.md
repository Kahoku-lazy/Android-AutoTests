## Why

DeepSeek 今日（2026-08-21）上线多模态视觉模型 **DeepSeek-V4-Flash-Vision-Exp**（API 模型 ID `deepseek-v4-flash-vision-exp`，OpenAI 兼容、支持 image_url 图像理解）。平台的智能体模型列表（deepseek 提供商）尚未收录，用户无法在配置页选中该模型测试视觉效果。

## What Changes

1. **P1** `frontend/src/modules/ai-assistant/helpers/model-config.ts`：`BUILTIN_MODELS.deepseek` 与 `CUSTOM_PROVIDER_MODELS.deepseek` 各补 `deepseek-v4-flash-vision-exp`。
2. **P1** `frontend/src/modules/ai-assistant/AgentDetail.vue`：providers 中 deepseek 的 `models` 数组同步补入。

图片通道无需改动：平台对话已支持图片上传（DataBlock → AgentScope openai formatter → image_url），视觉模型接入后即可直接看图。

无 **BREAKING** 变更。

## 关联文档

- `dev_docs/02-PRD需求/PRD-08-AI助手.md` §2.2（6 提供商内置模型列表）、§2.9（图片上传）
- DeepSeek 官方：[视觉理解指南](https://api-docs.deepseek.com/zh-cn/guides/vision/)
- 现场证据：前端 deepseek 模型列表仅 4 个（`model-config.ts:7`、`AgentDetail.vue:130-135`）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 模型列表同步（配置项补充），无需求级行为变化，`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 前端：`frontend/src/modules/ai-assistant/helpers/model-config.ts`、`AgentDetail.vue`（各 +1 行）
- 后端：无改动（model_name 无白名单校验，检测模型可自拉取）
- 测试范围：Vite dev 编译 200；配置页模型下拉出现该模型；选配后连接测试 /models 可通（用户自测）
