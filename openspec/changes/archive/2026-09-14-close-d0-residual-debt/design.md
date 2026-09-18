## Context

动机与逐条证据见 `proposal.md` - Why。本单是 D0 复查（`stabilize-drifted-index-names` 之后的第二单）的收尾批：把 D0 内「声明/文档/脚本」三处不一致收敛，并为唯一的 DB 直连登记例外。

## Goals / Non-Goals

**Goals:**

- `.env.example` 与「代码实际读取的 D0 开关」一一对应（可复制即用，不再需要读 settings.py 才知道有哪些开关）
- `run.py` 的静默忽略变为「有注释的显式忽略」+ 一行可诊断输出
- D0 唯一 DB 直连有正式登记（运维例外），不再与 D0 契约含糊冲突

**Non-Goals:**

- 不把 `cleanup_mysql_connections()` 搬出 D0（它依赖 `run.py` 已解析的 `BASE_ENV` 与子进程上下文，搬迁会引入新的耦合与子进程边界）
- 不改 `CORS_ALLOW_CREDENTIALS = True`（既有登记，生产侧已由 `CORS_ALLOW_ALL_ORIGINS=False` 兜住）
- 不改 `check --deploy` 的 5 条告警（本地 DEBUG 预期；生产默认已 fail-closed）
- 不把 `.env.example` 变成 `.env` 的完整镜像（只补 D0 开关与安全项）

## Decisions

### 1. `.env.example` 只补 5 个真开关，不补内部注入项

- **选择**：补 `DEVICE_ENGINE` / `AI_ENGINE` / `ADMIN_USERS` / `REDIS_URL` / `UPLOAD_CLEANUP_MAX_AGE_DAYS`
- **理由**：这 5 个是运维可配且代码读取的项；`DJANGO_ASGI_SERVER`（`run.py` 自行注入、`apps/ai_assistant/apps.py` 消费）属进程内部约定，写进示例反而会诱导手工设置，故不补

### 2. 空 except：注释 + 一行诊断，而不是抛错

- **选择**：`_kill` / 单连接 `KILL` 补注释；外层兜底 except 打印 `MySQL cleanup skipped: <原因>`
- **理由**：前两处失败是竞态（进程/连接已自行消失），抛错会破坏 stop 语义；外层失败需要留下线索（当前完全静默，MySQL 未启动时无人知道清理被跳过）

### 3. DB 直连登记在 ARCH-00 §七，而不是搬代码

- **选择**：在部署架构的关键开关块内加 3 行运维例外说明
- **理由**：D0 契约禁的是「业务逻辑 / 业务写库 / 业务查询」；该函数是 `run.py stop` 的 best-effort 运维清理（`information_schema` 元数据 + `KILL`），登记后口径明确，搬迁无收益

### 4. `test_settings.py` 删死赋值

- **选择**：删 `DB_ENGINE = "sqlite"`（保留 `DATABASES` 覆盖）
- **理由**：`settings.DB_ENGINE` 在测试侧无消费者（全仓引用清单可查）；真正生效的是紧随的 `DATABASES` 覆盖 —— 这正是 D0 治理线「零消费声明」的一类

## 模块防火墙自检

- 跨模块写库：不涉及（`run.py` 的 KILL 为既有运维动作，本单只登记 + 加诊断）
- 引擎边界 / 通信通道：不涉及

## Risks / Trade-offs

- [`.env.example` 新增项与服务端默认不一致] → 每个新增项都写明默认值与真相源（`DEVICE_ENGINE` 默认 u2、`AI_ENGINE` 默认 agentscope、`REDIS_URL` 优先于 HOST/PORT、清理默认 7 天）
- [`run.py` 多一行输出影响脚本输出解析] → 只在**异常分支**打印，正常路径无新增输出

## Migration Plan

1. 改 `.env.example` / `run.py` / `ARCH-00` / `test_settings.py` / 本地 `.env`
2. `manage.py check` + `makemigrations --check` + `ruff` + D0 单测 + `python run.py status` 冒烟
3. 归档；回滚 = `git checkout`（本地 `.env` 需手工恢复）
