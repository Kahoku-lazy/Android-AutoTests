## Why

知识库助手的语音/文字会话在页面挂机超过 1 小时后必然打不开：点「开始对话」弹出「会话出错 / 登录已过期或令牌无效，请重新登录」。后端日志实锤是 `知识库助手 WS 鉴权失败: Signature has expired`——access 凭证 1 小时过期，而 WebSocket 建连**只有一次 401 的等价物**、没有任何续期或重连机制：HTTP 请求有拦截器做「401 → 续期 → 重试」，WebSocket 走不到这条链路。页面本身又不发 HTTP 请求（`status` 只在首次进入拉取），所以 localStorage 里的过期凭证没有任何机会被换掉，点多少次都一样，只有整页刷新或去别的页面触发一次 401 才能恢复。

同一根因还带出两处体验问题：提示「请重新登录」是误导（真正需要的是换 access，refresh 还有 7 天）；前端与服务端对同一类错误有两套文案。

## What Changes

- 新增前端共享的**主动续期**入口 `shared/auth/token-refresh.ts`：`refreshAccessToken()`（单飞，同一时刻只发一次 `POST /api/auth/refresh/`）与 `ensureFreshToken()`（凭证已过期或将在 60 秒内过期时先续期）。HTTP 拦截器与 WebSocket 建连共用同一个单飞入口。
- 知识库助手**建连前**确认凭证有效：`start()` 先 `await ensureFreshToken()`，MUST NOT 带着已过期凭证建 WebSocket。
- 服务端以 4401 拒绝时，前端 MUST 自动续期并**重连一次**；重连成功 MUST NOT 向用户报登录过期；只有续期失败或重连仍被拒时才提示。
- **统一文案**：前后端对「登录过期」使用同一句，去掉误导性的「请重新登录」。
- 建连阶段收到的错误帧改为等 close 决定（成功重连时不把错误态写进页面），会话中途的错误仍立即呈现。
- 明确不做：不改成「每个请求前都预续期」（会改变拦截器同步签名，且刷新挂起会停住所有请求）；不改 access/refresh 的 TTL；不改 401→续期→重试的既有流程。

## 关联文档

- `PRD-平台总需求` 五、非功能约束 ·「实时性」与「安全」：任务进度走 HTTP 轮询；浏览器不持有模型服务商密钥。
- 既有规格 `auth-session`：公开认证端点 401 不触发刷新、续期失败无条件清空会话并跳登录页（本变更在其上补「主动续期」与「单飞」）。
- 既有规格 `knowledge-assistant-voice`：音频桥接要求的「通道 MUST 要求有效登录凭证」——本变更把「凭证过期后仍能继续用」补进该要求。
- 现场证据：`logs/backend.log` 的 `2026-11-06 16:09:48 知识库助手 WS 鉴权失败: Signature has expired`；15:06:24 一次续期签发的新 access 在 16:06 到期，期间无任何 HTTP 请求。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `auth-session`: 新增「访问凭证在过期前主动续期」要求（单飞续期入口、建连前确保证书有效、无续期凭证时不重试）。
- `knowledge-assistant-voice`: 改写「浏览器与实时模型之间的音频桥接」中的凭证条款——过期凭证先续期再建连、4401 自动重连一次、仅最终失败才提示。

## Impact

- 前端：新增 `frontend/src/shared/auth/token-refresh.ts`；改 `shared/api-client.ts`（续期改走共享入口）、`modules/knowledge-assistant/composables/useAssistantSession.ts`、`modules/knowledge-assistant/constants.ts`。
- 后端：`backend/apps/knowledge_assistant/consumer.py` 只改一句用户可见文案（不影响 4401 语义与「不建会话、不写日志」的行为）。
- 测试：新增 `frontend/tests/login/p0/tokenRefresh.spec.ts`、`frontend/tests/knowledge-assistant/p0/ws-auth-retry.spec.ts`；`tests/graybox/integration/test_knowledge_assistant_ws.py` 的断言与文案兼容，无需改。
- 非目标：不改令牌有效期；不做每请求预续期；不改 4401 的状态码语义。
