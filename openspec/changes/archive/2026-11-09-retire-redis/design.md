## Context

`db-backed-token-revocation` 已把吊销记录迁到 MySQL，Redis 现在只剩 `settings.py` 里一段「探测能用就用 Redis channel layer」的配置，而这段配置没有任何调用方（唯一 consumer 显式禁用 channel layer，全仓 0 处 `group_send`）。本设计只回答：退役的范围、为什么是固定 InMemory、以及怎么保证退役后没人被打断。

## Decisions

### D1 固定 InMemory，不保留「能连 Redis 就用」的自动探测

- 现状的探测只影响 `CHANNEL_LAYERS` 指向哪个后端，而没有任何代码取用 channel layer —— 探测的**唯一可观察效果**是启动日志可能多一行 warning。
- 固定 InMemory 后行为与当前实际行为完全一致（反正没人用），但配置更短、无外部依赖。
- 与测试环境（`tests/test_settings.py` 本来就把 channel layer 设成 InMemory）同构，减少「测试与生产不一样」的解释成本。

### D2 `run.py` 移除 redis 服务项，而不是留一个只打印的壳

- 留着壳会让 `run.py status` 显示一个 ONLINE 但零流量的服务，正是这次要消除的假象。
- `python run.py start redis` 不报「未知服务」而是打印「已退役」提示：对习惯旧命令的人友好，也不至于让 CI/脚本静默失败。
- `logs redis` 改为未知服务（历史 `logs/redis.log` 文件保留在磁盘，不删除）。

### D3 `requirements.txt` 删 `channels-redis` 与 `redis`

- 退役后全仓无 `import redis`，两包没有消费者；留着会让下一个接手的人以为 Redis 还有用。
- 风险：若将来重新引入 channel layer 后端，需要重装；这属于新变更的成本，不是遗留成本。

### D4 不主动杀现有 redis-server 进程

- `run.py` 只管自己启动的进程；现在有一个外部启动（或历史遗留下来）的 redis-server 仍在 6379。
- 它对本平台已无影响（0 调用）；是否停止由环境主人决定，写进人工验收步骤。
- 也避免误杀同机上其它项目共用的 Redis。

### D5 不动的部分

- 不改 `channels` 依赖、不改 ASGI 路由、不改 WS consumer 行为。
- 不改鉴权、吊销表、接口契约。
- 不删 `logs/redis.log`（历史日志，只影响磁盘，不影响运行）。

## Risks

| 风险 | 缓解 |
|---|---|
| 将来要做跨进程 WS 广播，InMemory 不跨进程 | 届时按新变更引入后端（Redis 或其它）；当前单 Daphne 进程，无广播调用 |
| 有人仍按旧习惯 `run.py start redis` | 打印退役提示，不静默失败 |
| 环境里 redis-server 继续空转 | 人工验收里给出停止命令；不影响平台 |
| `pip install -r requirements.txt` 后 `channels_redis` 缺失导致启动报错 | 已删除对应 import；门禁 `django-check` + `pytest-collect` 覆盖 |

## Migration Steps

1. `settings.py` 固定 InMemory，删 Redis 配置块。
2. `run.py` 摘除 redis 服务与相关分支。
3. `requirements.txt`、`.env.example` 清理。
4. 文档同步（README / ARCH / PRD / AGENTS / consumer docstring）。
5. 门禁 + `run.py start|stop|status` 冒烟。
