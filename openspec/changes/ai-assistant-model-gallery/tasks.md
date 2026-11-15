## 1. 后端接口

- [x] 1.1 新增模型卡片序列化：从 `engines.agents.models` 读 `available_models("chat")` + `get_model`，输出 `{name,label,provider,supports_image,thinking,context_size,ready}`，不返回密钥；验证：`test_ai_model_gallery.py::test_list_model_cards_only_chat_and_no_secret`
- [x] 1.2 新增 `GET /api/ai/models/`（登录可读）；验证：未登录 401 / 已登录 200 的单元测试
- [x] 1.3 新增 `POST /api/ai/chat/stream/`：入参 `{model, messages}`，`get_chat_model(model, stream=True)` 逐段输出 SSE（`data` / `event: done` / `event: error`），响应头含 `X-Accel-Buffering: no`；验证：`test_stream_chat_emits_delta_and_done`、`test_stream_chat_emits_error_event`
- [x] 1.4 注册 URL 与权限；验证：`python manage.py check` 通过，`reverse("ai:model_list")` 可解析

## 2. 前端数据层

- [x] 2.1 新增 `api/models.ts`：`listModels()` 走 `shared/api-client`；验证：`vue-tsc` 通过
- [x] 2.2 新增 `api/chat.ts`：fetch + `ReadableStream` 解析 SSE，暴露 `streamChat({model, messages, onDelta, signal})`；验证：类型检查通过、中断由 `AbortController` 触发
- [x] 2.3 在 `constants.ts` 补 `modelChatRoute`、provider 展示名与对话空态文案；验证：无硬编码

## 3. 前端页面

- [x] 3.1 新增 `components/ModelCard.vue` + `ModelCardGrid.vue`：名称/provider/能力徽章/上下文/就绪态，未就绪置灰不可点；验证：`vite build` 通过
- [x] 3.2 `index.vue` 改两栏布局：左角色卡、右模型卡；窄屏（≤960px）堆叠；验证：构建通过
- [x] 3.3 新增 `ChatPage.vue` 与路由 `/ai-assistant/chat/:model`：消息列表、流式追加、中断、错误提示、不可用兜底；验证：`vue-tsc` + `vite build` 通过

## 4. 测试与门禁

- [x] 4.1 后端单元测试：模型清单（只列 chat / 不泄密 / 401 / 200）、对话流（delta/done、error、未知模型 404、空消息 400）；验证：`python -m pytest tests/graybox/unit/test_ai_model_gallery.py -q` → 7 passed
- [x] 4.2 前端门禁：`npm run build:check`、`vue-tsc` 全绿；验证：构建产出含 `ChatPage` chunk
- [x] 4.3 更新 `frontend/src/modules/ai-assistant/AGENTS.md`：两栏布局、卡片只读、对话不持久化；验证：文档与实现一致
- [x] 4.4 跑本地门禁：`python run.py check`；验证：阻塞项全绿

## 5. 语音模型卡片与音色

- [x] 5.1 `models.yaml` 的 `omni` 增加可选音色；`ModelSpec` / loader / `describe_model` 支持 `voices`；验证：`test_ai_model_gallery.py::test_list_model_cards_covers_chat_and_realtime`
- [x] 5.2 卡片清单覆盖 realtime 族并带 `family` / `voice` / `voices`；语音卡片渲染音色下拉；验证：`npm run build:check` 通过
- [x] 5.3 点击语音卡片跳转 `/knowledge-assistant?mode=voice&voice=<音色>`；知识库助手前端把 query 拼进 WS 握手；验证：构建通过
- [x] 5.4 后端 consumer 解析并校验 `voice`，覆盖会话音色；非法音色返回可读错误；验证：`test_voice_from_scope_accepts_known_shape`
- [x] 5.5 修复视觉选路导致的参数类错配（`'Parameters' object has no attribute 'voice'`）；验证：`test_model_spec.py::test_vision_routing_uses_matching_parameters`

## 6. 卡池 + 统一对话页（改版）

- [x] 6.1 模型卡片去掉音色下拉，只展示能力与规格；点击统一进入对话页；验证：`npm run build:check`
- [x] 6.2 对话页顶部模型下拉：切换即清空当前会话；语音模型显示麦克风入口、隐藏文本输入；验证：`vue-tsc` + 构建通过
- [x] 6.3 对话流接口支持 `images`（≤4 张，`image/*` + base64），视图层校验模型能力，非视觉模型 400；验证：`test_validate_images_limits`、`test_view_rejects_images_for_text_model`、`test_build_messages_attaches_image_to_last_user_message`
- [x] 6.4 前端视觉模型支持选择图片、缩略图预览与移除；验证：`vue-tsc` + 构建通过
- [x] 6.5 模型卡不可点击、卡上无按钮；模型区标题右侧统一「对话」按钮进入对话页（初始 = 第一个就绪文字模型），无就绪模型时置灰；验证：`npm run build:check` 通过
