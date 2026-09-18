## 1. 模型列表同步

- [x] 1.1 `frontend/src/modules/ai-assistant/helpers/model-config.ts` 两处 deepseek 列表补 `deepseek-v4-flash-vision-exp`——验证 grep 命中 + Vite dev 编译 200
- [x] 1.2 `frontend/src/modules/ai-assistant/AgentDetail.vue` providers deepseek models 补同一 ID——验证 grep 命中 + Vite dev 编译 200

## 2. 验证与归档

- [x] 2.1 配置页模型下拉出现新模型（Vite dev 编译 200，页面 HMR 已生效；连接测试由用户自测）
- [x] 2.2 `openspec archive add-deepseek-vision-model` 归档本 change
