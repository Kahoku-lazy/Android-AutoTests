## 1. TTS 适配

- [x] 1.1 `pipeline_tts.py` 新增 `SambertTts`（WebSocket run-task、PCM 拼接、失败抛 RuntimeError）；验证：真实中文合成
- [x] 1.2 `config.py` 增加 `pipeline_tts_provider`、默认 `sambert` / `sambert-zhichu-v1` / 知厨，并保留 qwen 默认值；验证：配置单测
- [x] 1.3 `pipeline.py` 按 provider 选择 TTS，`ready` 显示新模型与音色；验证：Pipeline 端到端

## 2. 配置与文档

- [x] 2.1 `.env.example` 默认 Sambert，保留 Qwen-TTS 示例；验证：变量名与 config 一致
- [x] 2.2 更新引擎/前端 AGENTS 的 TTS 说明

## 3. 验证

- [x] 3.1 `sambert-zhichu-v1` 真实合成返回 PCM16 24k
- [x] 3.2 真实 WAV 走 Pipeline：用户转写 + DeepSeek 回答 + Sambert 音频；`ready.model` 为 sambert
- [x] 3.3 ruff / pytest / `manage.py check` / 前端 build
- [x] 3.4 `openspec validate switch-pipeline-tts-to-sambert --strict` 并归档
