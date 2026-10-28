## 1. 默认与提示词

- [x] 1.1 `config.py` 默认 mode/model 改为 omni + qwen3.5-omni-plus-realtime；livetranslate 保留显式选择；验证：配置/状态单测。
- [x] 1.2 `knowledge.py` 移除平台知识速览与回答约束，只保留直接对话提示；验证：提示词单测检查无平台速览。
- [x] 1.3 `.env.example` 默认 omni，并给 livetranslate 可选示例；本地 `.env` 切 omni；验证：状态接口 `mode=omni`。

## 2. 验证

- [x] 2.1 后端：`ruff` / `manage.py check` / 相关 pytest。
- [x] 2.2 前端：`typecheck` / `build`。
- [x] 2.3 真实语音问答：WAV 提问“设备管理里怎么连接一台安卓设备”，模型自由作答；`ready` 为 omni。
- [x] 2.4 `openspec validate default-omni-direct-dialogue --strict` 并归档。
