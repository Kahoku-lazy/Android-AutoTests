## 1. 页头文案

- [x] 1.1 将 `frontend/src/modules/ai-assistant/index.vue` 中 `VIEW_META` 四条 `title` 改为 `平台小助手` / `AI工具箱` / `知识库` / `评测中心`，并用 grep 确认该文件不再含 `Platform Assistant`、`AI Toolbox`、`Knowledge Base`、`Evaluation Center`

## 2. 回归核对

- [x] 2.1 全仓 grep 上述四个英文对照短语，确认无其它 AI 助手页头绑定；现有测试若未断言旧标题则无需改测
