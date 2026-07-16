# Security Rules — Android-AutoTests

> 在编写任何代码前，检查是否存在以下安全风险。发现风险时标注严重级别并给出替代方案。

## API Key 生命周期安全规则

API Key（如 DashScope/DeepSeek/OpenAI 密钥）是用户自行配置的第三方凭证，不是系统密钥。生命周期如下：

```
用户输入 → 加密写入 DB → 后端解密使用 → 前端脱敏展示 → 不可导出
```

### 写入（用户配置时）

```
[ ] create_agent / update_agent 必须调用 encrypt_key() 后再写入 DB
[ ] DB 中 api_key 字段值不以 "sk-" 开头（证明已加密）
[ ] update_agent 中检测 "***" 掩码 → 跳过更新（保留原值）
```

### 读取（前端展示时）

```
[ ] list_agents 列表接口不返回 api_key 字段
[ ] agent_detail 接口只返回 mask_key() 脱敏值（sk-***xxxx）
[ ] 查看完整 Key 需调用独立 reveal 接口，仅返回一次，5 秒后不可再获取
```

### 使用（后端调用 AI 时）

```
[ ] decrypt_key() 仅在 agent_factory.py / views.py 后端调用
[ ] 解密后的 Key 通过 AgentScope Tool 或 HTTP 请求体传给 AI 服务
[ ] 解密后的 Key 不写入日志、不返回给前端、不出现在错误消息中
[ ] decrypt_key() 解密失败时禁止 fallback 返回原文（当前 legacy 逻辑需移除）
```

### 导出（禁止）

```
[ ] 禁止任何 API 返回解密后的完整 api_key
[ ] 数据迁移/备份时 api_key 字段只导出加密值或跳过
[ ] register_agentscope_agents.py 等脚本不打印 api_key
[ ] WebSocket 消息不传输 api_key
```

### 检查清单

```
[ ] DB 中 SELECT api_key FROM ai_agents — 值不以 "sk-" 开头
[ ] GET /api/ai/agents — 响应中无 api_key 字段
[ ] GET /api/ai/agents/<id> — api_key 是脱敏值（sk-***xxxx）
[ ] 无任何端点返回完整 api_key（除 5s reveal 外）
[ ] decrypt_key() 解密失败不 fallback 返回原文
[ ] 日志/导出/备份中无 api_key 明文
[ ] SECRET_KEY 非默认值（加密有效性依赖此项）

## 风险分类标准

| 级别 | 判断依据 | 示例 |
|:--:|------|------|
| 🔴 严重 | 凭据直接可用 / 认证机制完全失效 / 数据无条件暴露 | 硬编码密码、无认证放行、Token 无验证 |
| 🟠 高 | 凭据可推导 / 权限缺失 / 用户数据未隔离 | 弱加密密钥、API 返回他人数据、无用户过滤 |
| 🟡 中 | 网络传输不安全 / 内部服务缺认证 / 日志泄露 | HTTP 明文密码、内网无 TLS、敏感字段打印 |
| 🟢 低 | 文档泄露 / 非敏感资源公开 / 配置暴露 | README 含凭据、Avatar 无认证访问 |

## AI 编码安全检查清单

编写代码时必须逐项自查：

### 凭据类（禁止硬编码）

```
[ ] 代码中无密码字符串（grep: admin123|autotests2026|password\s*=\s*'）
[ ] 代码中无 API Key 明文（grep: api_key\s*=\s*'[A-Za-z0-9]）
[ ] 代码中无数据库密码（grep: DB_PASSWORD|MYSQL_PASSWORD\s*=\s*'）
[ ] SECRET_KEY 从环境变量读取，不提供默认值
[ ] 前端表单不预填密码（禁止 ref('admin123')）
```

**遇到硬编码凭据时**：替换为 `os.environ.get('KEY_NAME', '')`，开发环境用空字符串，生产环境通过 .env 注入。

### 认证类（禁止绕过）

```
[ ] JWT 中间件无 token 时必须返回 401（非 user_id=None 放行）
[ ] WebSocket connect() 必须验证 JWT（非直接 accept()）
[ ] API 视图通过 request.user_id 识别用户（非忽略或硬编码）
[ ] logout 时 token 必须加入黑名单（确保 jti claim 已生成）
[ ] JWT 黑名单使用 Redis（非内存 set，避免重启丢失）
[ ] 自动化脚本从环境变量获取凭据（非硬编码 admin/admin123）
```

**遇到认证绕过时**：添加 JWT 验证，未认证请求返回 401；WebSocket 从 query string 提取 token 并 `verify_token()`。

### 数据隔离类（禁止跨用户访问）

```
[ ] 列表查询带 request.user_id 过滤（非查询所有用户数据）
[ ] 报告/导出文件下载验证文件所有者身份
[ ] WebSocket 推送按 user_id 隔离（非广播给所有连接）
[ ] API 返回数据不包含其他用户的测试结果、设备、用例
[ ] Task/Tool 执行中 user_id 从 context 获取（非硬编码 "ai_agent"）
```

**遇到数据泄露时**：在 ORM 查询中添加 `.filter(user_id=request.user_id)` 或关联过滤条件。

### 传输安全类

```
[ ] 生产环境启用 HTTPS（密码不通过 HTTP 明文传输）
[ ] CORS 不设置 ALLOW_ALL_ORIGINS = True（生产环境）
[ ] Redis 连接配置密码（生产环境，非空密码）
[ ] 服务间通信使用 TLS（非 localhost 部署时）
```

### 响应安全类

```
[ ] API 响应中 api_key 字段已脱敏（mask_key：sk-***xxxx）
[ ] 错误响应不包含堆栈、文件路径、SQL 语句
[ ] 日志中不输出 password、api_key、token 等敏感字段
[ ] 解密失败不 fallback 返回明文（decrypt_key 的 legacy 逻辑）
```

### 权限控制类

```
[ ] 新增 Tool 的 check_permissions() 使用 context.user_id 做身份验证
[ ] 只读 Tool 正确标记 is_read_only=True
[ ] 写操作 Tool 验证当前用户是否有操作目标资源的权限
[ ] 设备锁定只允许锁持有者释放
[ ] 删除操作考虑 HITL 二次确认（REQUIRE_USER_CONFIRM）
```

### 文件安全类

```
[ ] .env 已在 .gitignore 中
[ ] .gitignore 包含 dump.rdb、data/、logs/、exports/
[ ] 不提交含真实设备序列号、API Key 的配置文件
[ ] 上传的文件仅所有者可访问（非公开 URL）
```

## 代码评审时的风险判断流程

```
发现一段代码
 ├── 有密码/密钥字符串？
 │   └── 是 → 🔴 严重：替换为环境变量
 ├── DB 中 api_key 是明文（sk- 开头）？
 │   └── 是 → 🔴 严重：确认 SECRET_KEY 非默认值，重新加密存储
 ├── SECRET_KEY 是默认值？
 │   └── 是 → 🔴 严重：设置 DJANGO_SECRET_KEY 环境变量
 ├── 有认证检查被注释/跳过？
 │   └── 是 → 🔴 严重：恢复认证逻辑，加环境变量开关
 ├── 查询数据没按 user_id 过滤？
 │   └── 是 → 🟠 高：添加用户过滤条件
 ├── API 响应包含 api_key/password？
 │   └── 是 → 🟠 高：脱敏或移除
 ├── WebSocket accept() 无 token 验证？
 │   └── 是 → 🔴 严重：添加 JWT 验证
 ├── 日志中有敏感字段？
 │   └── 是 → 🟡 中：移除敏感字段
 └── 文档中有默认密码？
     └── 是 → 🟢 低：替换为"请替换为实际密码"
```

## 敏感字段黑名单

以下字段**禁止**出现在代码文本、日志输出、API 响应、错误消息中：

```
password   passwd    pwd       api_key    apikey
secret     token     SECRET_KEY  DB_PASSWORD
MYSQL_PWD  REDIS_PWD  private_key
```
