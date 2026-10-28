## 1. 引擎

- [x] 1.1 `config.py` 增加 `pipeline` 模式、`select_mode()`、pipeline LLM/TTS 配置与校验；验证：配置模式选择单测
- [x] 1.2 新增 `pipeline_llm.py`：DeepSeek Flash 流式回答 + 多轮历史；验证：真实 DeepSeek 调用
- [x] 1.3 新增 `pipeline_tts.py`：Qwen-TTS HTTP 返回 WAV 转 24k PCM16；验证：真实 TTS 返回可播放 PCM
- [x] 1.4 新增 `pipeline.py`：ASR 事件循环、用户转写、DeepSeek、TTS、打断、日志；验证：真实 WAV 走通
- [x] 1.5 `LiveTranslateRealtimeModel` 支持 `output_modalities=["text"]` 作为 ASR；验证：ASR 只出源语

## 2. 接入

- [x] 2.1 consumer 读取 `mode` 查询参数，按模式选择 `RealtimeVoiceSession` / `PipelineVoiceSession`；验证：omni 与 pipeline 各建一次连接
- [x] 2.2 更新 `.env.example` 与模块 AGENTS；验证：变量名与 config 一致

## 3. 前端

- [x] 3.1 增加路线选择器（Omni 直连 / ASR + DeepSeek + TTS），`start(mode)` 带 `mode` 查询；验证：typecheck/build
- [x] 3.2 页面副标题模式行随路线变化；验证：浏览器截图
- [x] 3.3 保留麦克风设备选择器

## 4. 验证

- [x] 4.1 ruff / pytest / `manage.py check`
- [x] 4.2 真实 WAV：pipeline 跑通用户转写 + DeepSeek 回答 + TTS 音频；`ready` 带 pipeline
- [x] 4.3 `openspec validate add-pipeline-voice-mode --strict` 并归档
