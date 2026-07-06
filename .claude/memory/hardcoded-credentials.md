---
name: hardcoded-credentials
description: 代码中禁止硬编码密码/API Key/Token
metadata: 
  node_type: memory
  type: project
  originSessionId: b05814f4-5f5d-4bc7-9238-26a81baf151e
---

禁止在代码中出现：
- 密码字符串：`admin123`、`autotests2026` 等
- API Key 明文：`sk-...`、`api_key = 'xxx'`
- 数据库密码：`DB_PASSWORD = 'xxx'`
- SECRET_KEY 默认值

正确做法：`os.environ.get('KEY_NAME', '')`，开发环境用空字符串，生产通过 .env 注入。

`.claude/hooks/protect-credentials.sh` 在每次 Edit/Write 前自动扫描这些模式并阻断。详见 [[security-rules]]。

**Why:** 历史最高频问题（5+ 次 🔴 严重），一旦提交到 git 历史难以彻底清除。

**How to apply:** 写代码前过一遍 `.claude/rules/security.md` §凭据类检查清单。hook 自动阻断是最后防线，但不应依赖它——应该在写的时候就避免。
