## 1. 引擎适配器

- [x] 1.1 新增 `engines/agents/realtime_vocie/livetranslate.py`：模型卡、`Parameters`、`connect`、`session.update`、事件映射、`session.finish`；验证：协议单测通过。
- [x] 1.2 `config.py` 增加 `mode` / `translation_language`、默认 `qwen3.8-livetranslate-flash-realtime`、mode/模型推断与冲突拒绝；验证：配置单测通过。
- [x] 1.3 `create_realtime_model` 按 mode 选择 `LiveTranslateRealtimeModel` 或 `DashScopeRealtimeModel`；验证：模型选择单测通过。
- [x] 1.4 `session.py` 的 `ready` 事件带 `mode` / `translation_language`；验证：真实 WAV 链路 ready 字段正确。

## 2. 前端与配置

- [x] 2.1 前端状态/ready 类型增加 mode/translation_language；页面副标题与「模式」行随模式变化；验证：typecheck / build。
- [x] 2.2 `.env.example` 默认 livetranslate，并给出 omni 回退注释；验证：变量名与 `config.py` 一致。

## 3. 验证

- [x] 3.1 后端：`ruff check` / `ruff format --check` / 相关 pytest。
- [x] 3.2 前端：`npm run typecheck` / `npm run build`。
- [x] 3.3 真实 WAV：默认 livetranslate 跑通源语转写 + 中文译文；`ready` 的 mode/model 正确。
- [x] 3.4 `openspec validate switch-realtime-model-to-livetranslate --strict` 并归档。
