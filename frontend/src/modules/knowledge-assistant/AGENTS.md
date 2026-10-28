# knowledge-assistant 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件（本文件只写增量）。

## 入口与布局

- 路由 `/knowledge-assistant`（`routes.ts`）；侧栏「AI 功能」分组第二项，文案「知识库助手」。
- 页面 = `WorkbenchHeader` + 两栏：左侧 `VoiceConsole`（粘性语音台）、右侧 `TranscriptPanel`（对话记录）。纵向滚动只留在 `.doc-body`，面板内部不滚动。
- 页面根带 `wb-shell`；空态用 `EmptyState`、错误用 `ErrorState`、加载用 `SkeletonCard`，不新增第二套卡片/按钮皮肤。

## 语音链路

- 点击语音按键后才申请麦克风并建立 `/ws/knowledge-assistant/?token=...`；不得自动启动。
- 默认路线 `omni`（`qwen3.5-omni-plus-realtime` · Tina）；前端「路线」选择器可切 `pipeline`（ASR + DeepSeek Flash + Sambert 知厨 TTS），并通过 WS query `mode` 传给后端。页面副标题与「模式」行随路线变化。
- 文本输入框挂在右侧「对话记录」面板底部，仅 `pipeline` 路线显示；发送文字时若未开始会话，自动建立不申请麦克风的纯文本会话（播放器 + WS 仍建立），再发 `{type:"text",text}`。
- 上行：`MicCapture`（AudioWorklet，ScriptProcessor 兜底）→ 固定 100ms 分块 → 重采样到 `ready.input_sample_rate` → Int16 PCM 二进制帧。
- 下行：JSON `audio_item` 标记条目 → 二进制 PCM16 → `AudioPlayer` 按 `ready.output_sample_rate` 播放。
- 打断：发送 `{"type":"interrupt"}`；服务端回 `clear_audio` 时清空播放队列。播放进度每 200ms 回传 `played`。

## 红线

1. **不直连模型服务商**：浏览器只连本平台 WS；API Key 不得进入前端。
2. **RAG 只做后端检索**：本页不提供文档上传、知识库文档列表或检索管理入口；RAG 由后端 `engines/agents/rag` 读取本地资料并注入 Pipeline LLM。
3. **不在组件里写解析算法**：音频转换在 `audio/pcm.ts`，消息归并在 `helpers/transcript.ts`，组件只渲染与发事件。
4. **不新增第二套 WS**：本模块只使用 `/ws/knowledge-assistant/`；任务进度仍走 HTTP 轮询。
5. **样式令牌**：颜色/字号/间距/圆角/阴影/动效只取 `shared/styles/tokens.css`；圆形按键的 `50%` 属已登记图形量。

## 快速验证

```powershell
cd frontend
npm run lint:styles
npm run typecheck
npx vitest run knowledge-assistant
```
