## 1. 账本

- [x] 1.1 新建 `usage_ledger` App、`ModelUsage` 表 `ai_usage_records` 与迁移
- [x] 1.2 `pricing.json` + `pricing.py`：DeepSeek / DashScope / TTS / Embedding / ASR 价目，未收录模型标 `unpriced`
- [x] 1.3 `api.py`：幂等写入、语音事件入账、分厂商汇总、最近明细

## 2. 写入

- [x] 2.1 任务 `event_store` 写入 `usage_id` 与账本
- [x] 2.2 语音 `DialogueLog` 旁路入账；consumer 用线程池写 ORM
- [x] 2.3 语音记录 model/asr/tts/embedding 用量

## 3. 仪表盘

- [x] 3.1 dashboard stats 返回 `usage_ledger`
- [x] 3.2 前端模型用量分类卡片 + 最近明细表
- [x] 3.3 卡片副标题显示厂商；分类覆盖 LLM/TTS/Realtime/Embedding/ASR

## 4. 验证

- [x] 4.1 价目/幂等/分类单测
- [x] 4.2 语音文本提问产生账本记录并出现在仪表盘
- [x] 4.3 ruff / pytest / manage.py check / 前端 build
- [x] 4.4 `openspec validate add-model-usage-ledger --strict` 并归档
