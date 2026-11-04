# knowledge-assistant 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件（本文件只写增量）。

## 入口与布局

- 路由 `/knowledge-assistant`（`routes.ts`）；侧栏「AI 功能」分组第二项，文案「知识库助手」。
- 页面 = `WorkbenchHeader` + 两栏：左侧 `VoiceConsole`（粘性语音台）、右侧 `TranscriptPanel`（对话记录）。纵向滚动只留在 `.doc-body`，面板内部不滚动。
- 页面根带 `wb-shell`；空态用 `EmptyState`、错误用 `ErrorState`、加载用 `SkeletonCard`，不新增第二套卡片/按钮皮肤。

## 会话方式

- 左侧先选「语音 / 文字」，再点「开始对话」；一次会话只有一种方式，切换方式必须先结束当前会话（未结束时给出提示，不静默切换）。
- 方式决定连接参数：语音 `mode=voice`，文字 `mode=text`；两种方式共用同一条 `/ws/knowledge-assistant/` 与同一份对话记录。

## 语音链路

- 点击语音按键后才申请麦克风并建立 `/ws/knowledge-assistant/?token=...&mode=voice`；不得自动启动。
- **仅 Omni + 知识库问答**：`qwen3.5-omni-plus-realtime` · Tina；无路线选择器；后端注入 RAG 检索工具。
- 上行：`MicCapture`（AudioWorklet，ScriptProcessor 兜底）→ 固定 100ms 分块 → 重采样到 `ready.input_sample_rate` → Int16 PCM 二进制帧。
- 下行：JSON `audio_item` 标记条目 → 二进制 PCM16 → `AudioPlayer` 按 `ready.output_sample_rate` 播放。
- 打断：发送 `{"type":"interrupt"}`；服务端回 `clear_audio` 时清空播放队列。播放进度每 200ms 回传 `played`。

## 文字链路

- 文字方式不申请麦克风、不建 `AudioPlayer`；连接直接带 `mode=text`，一次连接一个 DeepSeek Flash 会话。
- 上行只有 `{"type":"text","text":"..."}`；回答仍以 `reply_start` / `transcript_delta` / `transcript_final` / `reply_end` 下发，页面复用同一套消息归并。
- 文字模型是 `deepseek-flash`，检索仍由后端 `search_knowledge` 工具完成；语音与文字**不共享上下文**。
- 生成中再发送会被拒绝并提示；输入框只在文字方式、已连接、无回答进行中时可发送。

## 红线

1. **不直连模型服务商**：浏览器只连本平台 WS；API Key 不得进入前端。
2. **RAG 只做后端检索**：本页不提供文档上传、知识库文档列表或检索管理入口；RAG 由后端 `engines/agents/rag` 读取本地资料并注入 Omni 会话。
3. **不在组件里写解析算法**：音频转换在 `audio/pcm.ts`，消息归并在 `helpers/transcript.ts`，方式/状态文案与发送门控在 `helpers/mode.ts`，组件只渲染与发事件。
4. **不新增第二套 WS**：本模块只使用 `/ws/knowledge-assistant/`；任务进度仍走 HTTP 轮询。
5. **样式令牌**：颜色/字号/间距/圆角/阴影/动效只取 `shared/styles/tokens.css`；圆形按键的 `50%` 属已登记图形量。
6. **不得重新引入** pipeline / livetranslate 路线；文字问答 MUST 走 `mode=text` + DeepSeek Flash，不得借输入框复活 Pipeline / TTS 链路。

## 快速验证

```powershell
cd frontend
npm run lint:styles
npm run typecheck
npx vitest run knowledge-assistant
```
