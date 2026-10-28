## 1. 修复

- [x] 1.1 后端状态接口增加 pipeline LLM/TTS/voice 字段
- [x] 1.2 前端 `modelLabel` 按所选路线显示；会话开始后仍用实际值
- [x] 1.3 补充状态字段断言

## 2. 验证

- [x] 2.1 页面切换到 Pipeline、未开始时模型行立即变化
- [x] 2.2 ruff / pytest / typecheck / build
- [x] 2.3 `openspec validate fix-pipeline-route-model-label --strict` 并归档
