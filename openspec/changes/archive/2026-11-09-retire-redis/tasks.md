## 1. 配置

- [x] 1.1 `backend/config/settings.py`：`CHANNEL_LAYERS` 固定为 `channels.layers.InMemoryChannelLayer`，删除 `_channel_layers_config()`、`REDIS_HOST` / `REDIS_PORT` / `REDIS_URL`。验证：`manage.py check` 通过；`grep -rn "REDIS_" backend/` 为 0。
- [x] 1.2 `requirements.txt`：删除 `channels-redis>=4.0` 与 `redis>=5.0`。验证：全仓 `import redis` / `channels_redis` 0 命中（只剩注释里的历史说明）。

## 2. 运维脚本

- [x] 2.1 `run.py`：`SERVICE_ORDER` / `SERVICES` / `_START` / `_STOP` / `_LOGS` 去掉 `redis`；删除 `start_redis()` / `stop_redis()`；`cmd_start` / `cmd_restart` 去掉 `if s != "redis"` 特判；`cmd_status` 去掉 Redis 行；usage 与 argparse help 同步。顺带删除因此失去调用方的 `port_in_use()` 与 `import socket`。验证：`python run.py status` 只打印 backend/frontend。
- [x] 2.2 `resolve_services()`：`redis` 不再算未知服务，打印「已退役」提示后忽略（提示用英文，与 run.py 其它输出一致，避免 Windows 管道编码歧义）。验证：`python run.py start redis` → exit 0 + `Note: Redis is retired ...`。
- [x] 2.3 `cmd_start` 的启动横幅去掉 `Redis : redis://...` 行。验证：`python run.py start redis` 输出无 Redis 地址。

## 3. 文档与环境样例

- [x] 3.1 `.env.example`：删除 Redis 段。验证：文件内无 `REDIS`。
- [x] 3.2 `README.md`：本期范围、架构图、数据表、环境要求、启动命令注释、`run.py status` 文案、`logs/` 清单、环境变量样例说明同步。验证：`README.md` 内 `Redis` 只剩「已退役」这一处事实描述。
- [x] 3.3 `dev_docs/ARCH_PRD/ARCH-平台架构设计.md`：技术栈、总览图、进程表、外部依赖、模块表同步。
- [x] 3.4 `dev_docs/ARCH_PRD/PRD-平台总需求.md`：数据行改为「平台无外部 KV 依赖」。
- [x] 3.5 `backend/apps/AGENTS.md` 删掉「依赖 Redis」的过时表述；`backend/apps/knowledge_assistant/consumer.py` 的「不接 channel layer」说明改为「历史实现用 Redis 时……」的表述。

## 4. 测试

- [x] 4.1 `tests/test_settings.py`：直接删掉 `CHANNEL_LAYERS` 覆盖（正式配置已是 InMemory），测试与生产同构。验证：`-m auth` 36 条全绿。
- [x] 4.2 回归：`tests/graybox/unit -m auth` **36 passed**；知识库助手 WS 用例（`test_knowledge_assistant_ws.py` + `test_knowledge_assistant_consumer.py`）**12 passed**。

## 5. 收口

- [x] 5.1 门禁：`python run.py check` → **阻塞项 23/23 通过**，0 失败（告警项仍是既有的 23 条 engines docstring）。
- [x] 5.2 冒烟：`python run.py status` 只显示 backend/frontend；`python run.py start redis` 打印退役提示且 exit 0；`SERVICE_ORDER = ('backend','frontend')`、`RETIRED_SERVICES = ['redis']`。
- [ ] 5.3 人工验收（用户）：平台登录/登出、知识库助手文字问答正常；按需手动停止本机遗留的 redis-server（`Stop-Process -Name redis-server`）与清理 52 个 `jwt:session_revoked:*` 旧键，确认平台无异常。
