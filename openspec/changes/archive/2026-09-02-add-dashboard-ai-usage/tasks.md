## 1. ai_assistant：token 用量落库

- [x] 1.1 `models.py` 新增 `cache_input_tokens`/`cache_creation_input_tokens` 字段，并生成迁移。验证：`python manage.py makemigrations --check` 提示需迁移且 `ruff check apps/ai_assistant/models.py`
- [x] 1.2 `chat_views._agent_stream` 捕获 `MODEL_CALL_END` 的 input/output token，终端时随 `save_message` 持久化（`tokens`=输出、`input_tokens`=输入、`model_name`）。验证：`ruff check apps/ai_assistant/views/chat_views.py`

## 2. ai_assistant：缓存命中落库

- [x] 2.1 新增 `UsageCaptureMiddleware`（`on_model_call` 捕获 `ChatUsage.cache_*` 写入 per-session 注册表），在 `agent_factory.build_agent` 装配，`_agent_stream` 终端读取并落库。验证：`ruff check apps/ai_assistant/agent_scope/`
- [ ] 2.2 DeepSeek 缓存字段兜底：子类化 `OpenAIChatModel` 的 usage 转换以同时读 `prompt_cache_hit_tokens`。验证：真实对话后查 `ai_messages.cache_input_tokens` 非 0（DeepSeek 视觉模型）——**延后**：需子类化流式模型方法，风险高；当前 DeepSeek 经 OpenAIChatModel 读 `cached_tokens`，命中率暂为 0/—

## 3. dashboard：AI 用量聚合

- [x] 3.1 `apps/dashboard/views.py` 新增 `_ai_usage_stats()` 只读聚合，`stats` 响应加 `ai_usage` 字段（今日/累计）。验证：`python tools/gen_arch_stats.py --check-boundaries` 0 违规 + `ruff check apps/dashboard/views.py`

## 4. 前端：AI 用量区块

- [x] 4.1 `shared/types/dashboard.ts` 增加 `ai_usage` 类型；`DashboardView.logic.ts`/`useDashboardStats.ts` 映射数据。验证：`npm run typecheck`（ai-assistant/dashboard 无新增报错）
- [x] 4.2 `index.vue` 新增「AI 用量」区块 + 卡片（对话总数/累计 Token/缓存命中率/平均每对话 Token，今日+累计）。验证：`npm run typecheck` + 真实页面骨架屏/滚动动画正常

## 5. 全链路验证与门禁

- [ ] 5.1 真实对话若干轮后刷新仪表盘，确认「AI 用量」四卡今日/累计数值与 `ai_messages` 聚合一致。验证：人工 E2E
- [ ] 5.2 后端 `manage.py check` + `ruff` 全通过（环境修复后）；`gen_arch_stats --check-boundaries` 0 违规
