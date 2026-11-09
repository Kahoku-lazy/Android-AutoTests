## Why

`db-backed-token-revocation` 把登出吊销记录迁到 MySQL 之后，Redis 在平台里已经**没有任何调用方**：

- 代码层：只有 `backend/config/settings.py` 的 `_channel_layers_config()` 会 `import redis` / 构造 `RedisChannelLayer`；全仓无 `get_channel_layer()`、无 `group_send`、无 `redis.from_url`。
- 运行时实测：连续 5 次登录 + 10 个受保护请求，Redis `total_commands_processed` 只增加 1（那 1 次是人工执行的 `INFO`）。
- 唯一的 WS consumer 显式 `self.channel_layer = None`，并写明「不接 channel layer」。

但它仍然以「平台三件套」的身份被 `run.py` 启动、占着 6379、在 `.env.example` 里要求配置、在 `requirements.txt` 里拉两个包（`channels-redis`、`redis`）。这是一种「启动成功但毫无用处」的假象，运维上多一个必须常驻、必须开持久化的进程。

## What Changes

- `backend/config/settings.py`：`CHANNEL_LAYERS` 固定为 `InMemoryChannelLayer`，删除 `REDIS_HOST` / `REDIS_PORT` / `REDIS_URL` 与自动探测函数。
- `run.py`：`SERVICE_ORDER` / `SERVICES` / `_START` / `_STOP` / `_LOGS` 去掉 `redis`；删除 `start_redis()` / `stop_redis()`；`status` 不再打印 Redis；`start redis` 改为打印「已退役」提示而不是报未知服务。
- `requirements.txt`：删除 `channels-redis` 与 `redis`。
- `.env.example` / `README.md` / `dev_docs/ARCH_PRD` / `backend/apps/AGENTS.md` / 知识库助手 consumer 的说明：同步为「无 Redis」。
- 不动的部分：`channels` 依赖、WS 通道本身、鉴权与吊销逻辑、数据库。

## Impact

- **对用户与接口零影响**：没有 API、页面或数据变化；登录/登出/WS 问答路径不变。
- **运行方式变化**：`python run.py start` 只启动 backend + frontend；`python run.py status` 不再有 Redis 行；`logs redis` 失效（保留 `logs/redis.log` 历史文件）。
- **已运行的 redis-server 进程不会被本变更停掉**：`run.py` 只是不再管理它，需要手动停止（见 tasks 的人工验收）。
- **能力边界**：单进程 Daphne 下 `InMemoryChannelLayer` 足够；将来若要做跨进程 WS 广播，需要重新引入一个 channel layer 后端（届时按 OpenSpec 新单处理）。
