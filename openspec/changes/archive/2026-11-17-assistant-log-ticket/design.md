## Context

报告 HTML 的截图是内联 base64，字体是相对路径。`window.open` 带不上登录头。把 JWT 放进 URL 会进历史。blob 打开会让相对字体失效。动机见 proposal.md。

## Goals / Non-Goals

**Goals:**

- 换票接口仍走登录头。
- 打开报告只用一次性 ticket。
- 报告文件与字体相对路径不变。

**Non-Goals:**

- 不改日志目录与 HTML 内容。
- 不把 ticket 持久化到数据库。
- 不支持把链接发给未登录的人长期查看。

## Decisions

### 1. 进程内一次性凭证

换票生成随机 ticket，登记 `thread_id`、`report_id`、过期时刻。打开时校验并立即删除。进程重启后未使用的 ticket 失效，用户重新点「查看」。不新建表。

备选是签名 URL 不落状态。否决：无法保证只用一次，除非仍要服务端记已用集合。记一次和记 ticket 一样，直接记 ticket 更简单。

### 2. 60 秒只约束开门

过期判断发生在打开请求。响应开始后不再计时。刷新页面会重新请求，旧 ticket 已作废，需要再换一张。

### 3. 前端先换票再打开

「查看」调用换票接口，再用返回的 ticket 调 `window.open`。不把 JWT 放进查询串。

## 模块防火墙自检

- 换票与验票都在 `ai_assistant/api.py`。
- 不把磁盘路径放进 ticket。
- 前端只经 `api/assistants.ts`。

## Risks / Trade-offs

- [多进程时 ticket 只在签发进程] → 本期与现有取消令牌一样，接受单进程。
- [60 秒内未打开] → 用户再点一次「查看」。
