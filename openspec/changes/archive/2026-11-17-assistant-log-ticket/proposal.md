## Why

对话栏用 `window.open` 打开 HTML 报告时带不上登录头，无头请求返回 401。把登录令牌放进 URL 会进浏览器历史。需要一次只开一扇门的短时凭证，且不改报告里的相对字体路径。

## What Changes

- 点「查看」先用已登录请求换一张一次性 ticket。ticket 只含报告编号与过期时间，不含磁盘路径。
- ticket 的有效期是开门时间，默认 60 秒。在此期间打开一次即作废。页面加载完成后可以继续看，不受 60 秒限制。
- 打开报告的地址带 `ticket`，不带登录头。用过、过期、不属于该栏或该报告，一律拒绝。
- 进行中的一轮不发 ticket。
- 不改 HTML 内容，不把报告读成 blob。字体相对路径保持可用。
- 不改 SOP，不改日志目录。

## 关联文档

无。`dev_docs/ARCH_PRD/PRD-平台总需求.md` 不覆盖助手报告的打开凭证。

## Capabilities

### New Capabilities

- `assistant-log-ticket`: 助手报告的一次性开门凭证：60 秒内打开一次，打开后可继续看。

### Modified Capabilities

- `assistant-thread-log`: 查看已完成报告时，浏览器打开必须能在不携带登录头的情况下通过一次性凭证完成；直接无凭证打开仍拒绝。

## Impact

- 后端：`backend/apps/ai_assistant` 增加换票与验票。不新增表，凭证放进程内，过期即丢。
- 前端：`frontend/src/modules/ai-assistant` 的「查看」先换票再 `window.open`。
- 测试：无票 401、过期拒绝、用过一次后再开拒绝、进行中不发票。
