---
name: no-retry-loop-on-blocked-commands
description: 安全分类器持续拦截命令时禁止重复尝试，必须立即停止并告知用户
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 20404476-773d-49d5-b645-8aafe1b0106f
---

如果同一个命令被安全分类器（deepseek-v4-pro）连续拦截超过 2 次，**禁止继续尝试**。必须立即停止并告知用户手动执行。

**Why:** 2026-07-14 启动 http.server 时被 deepseek-v4-pro 连续拦截多次，每次都阻塞 5-10 秒，浪费时间且最终仍无法执行。分类器不可用时重试不会改变结果。

**How to apply:** 任何 Bash 命令被拒 2 次后，不再尝试第 3 次。直接告诉用户命令内容和手动执行方式。如果是非关键命令（如启动服务器），优先让用户手动跑。
