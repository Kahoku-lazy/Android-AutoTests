## Why

D0 复检发现 4 项**配置失真与重复实现**（均为实测，非推测）：

| # | 位置 | 现象 | 证据 |
|---|------|------|------|
| 4 | `config/settings.py:334` | `JAZZMIN_SETTINGS["custom_css"] = "css/admin-fonts.css"` 指向**不存在的文件** | `**/admin-fonts.css` 全仓 0 命中；`static/` 目录只有 `.gitkeep` → 后台每次请求该 CSS 都 404 |
| 5 | `config/settings.py:349-382` | `LOGGING` 只在 `DOCKER_CONTAINER` 为真时定义，而该变量**全仓仅此一处引用**、仓库内**无 Dockerfile / docker-compose**；全仓也无 `basicConfig`/`dictConfig` | 部署实际运行时 `LOGGING` 从未生效；应用级 `logger.info` 无 handler（仅 `logging.lastResort` 输出 WARNING+），`run.py:162-172` 重定向到 `logs/backend.log` 也拿不到 INFO |
| 6 | `config/api_docs.py`（683 行） | D0 内**手写的第三份 API 真相源**，已与代码脱节：36 条 `"path":` 条目 vs 实测 116 条路径条目；`:490` 仍写已删除的 `/ws/screenshot`（WS 生产点现为 0）；`:439` 仍把 test_runner 列为聚合来源 | `temper` 实测计数 + ARCH-00 上轮修订；真相源实为各 App `urls.py` 与 `/api/schema` |
| 7 | `config/settings.py:21-33` vs `run.py:31-43` | `.env` 解析在 D0 内**有两份近乎重复的实现**，引号处理还不一致（`.strip('"').strip("'")` vs `.strip("\"'\")`） | 两份代码逐行比对 |

## What Changes

1. **#4 删掉失效的 `custom_css` 键**：该文件从未存在，键从未生效；删除即「恢复到真实行为」。若确实要中英文字体覆盖，属主题/前端需求，另立变更（登记为范围外）。
2. **#5 让日志配置无条件生效**：把 `LOGGING` 从「仅容器」改为**始终定义**，本地/容器只在 handler（文件 vs stdout）与格式上分档；日志级别由 `LOG_LEVEL` 环境变量控制（默认 `INFO`）。`DOCKER_CONTAINER` 补进 `.env.example` 并说明作用。
3. **#6 给手写 API 文档加上「不许静默漂移」的机检**：
   - 修掉已失效内容（`/ws/screenshot` 条目、test_runner 聚合表述）；
   - 文件头写明它是**人工维护的公开文档快照**，真相源是各 App `urls.py` 与 `/api/schema`；
   - 新增一致性测试：把 `api_docs.py` 的 `path` 条目集合与 `config/urls.py` + 各 App `urls.py` 的实际路径集合比对，**漂移即失败**（给出「文档漏收录 / 收录了已不存在的端点」双向断言）。
   - 「彻底改由 drf-spectacular schema 渲染 `/api/docs`」登记为后续决策（依赖 schema 补齐单）。
4. **#7 收敛 `.env` 解析为单一实现**：新增 `config/env.py::load_dotenv()`（D0 内纯标准库，无 Django 依赖），`config/settings.py` 与 `run.py` 都改调用它，删除两份重复实现。

## 关联文档

- 取证：`temps/scan_d0.py`（settings 符号消费数 + `.env.example` 键读取方）· `python -m ruff format --diff config/settings.py`
- 代码：`config/settings.py` · `config/api_docs.py` · `config/urls.py` · `run.py`
- 前序：`openspec/changes/archive/2026-09-14-remove-dead-d0-config/`（同一 D0 治理线，本单继续收敛「配置与代码不一致」）
- 范围外登记：`/api/docs` 改由 schema 渲染（依赖 `complete-openapi-schema`）· 后台字体覆盖需求

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无；`.openspec.yaml` 已声明 `skip_specs: true`）

## Impact

- **修改**：`config/settings.py` · `config/api_docs.py` · `run.py` · `.env.example`
- **新增**：`config/env.py`（单一 `.env` 解析实现）· 一致性测试（`tests/graybox/unit/test_api_docs_consistency.py`）
- **不影响**：API 契约与响应、前端、DB、`apps/` 业务逻辑、公开前缀策略
- **测试范围**：`manage.py check` · 日志生效用例（caplog 断言 INFO 可达）· API 文档一致性用例 · `pytest -m "unit or integration"` · `ruff` · `--check-boundaries`
