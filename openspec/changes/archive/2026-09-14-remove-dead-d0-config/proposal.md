## Why

D0（边界与配置）实测有 **5 个零消费符号**，它们让「D0 只放被消费的装配配置」这一层契约失真，并持续误导接手者以为平台存在一个独立的 AgentScope 服务：

- `config/agentscope_config.py`（62 行）全仓 **0 引用**（连文件内容里都没有自己的模块名）；
- `AGENTSCOPE_SERVICE_{PORT,URL,TITLE,VERSION}` 中 `..._URL` 零消费，其余三项只被上面那个死模块读；
- `AGENTSCOPE_WORKSPACE_DIR` 同样只被死模块读；
- `AIRTEST_ENABLED` 代码零消费（仅 ARCH-00 文档提及，test_runner 已下线）；
- `SCREENSHOT_INTERVAL` 零消费（截图流已快照化）。

已确认 `openspec/specs/` 对以上符号**零引用**，故这是纯删除、无行为变化。

## What Changes

- 删除死模块 `config/agentscope_config.py`（62 行）。
- 删除 `config/settings.py` 的整个 `# ── AgentScope ──` 块（`AGENTSCOPE_SERVICE_PORT/URL/TITLE/VERSION` + `AGENTSCOPE_WORKSPACE_DIR`，共 5 项）。
- 删除 `AIRTEST_ENABLED`（含其上注释行）与 `SCREENSHOT_INTERVAL`。
- 同步 `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md` §七「关键开关（环境变量）」：移除 `AIRTEST_ENABLED` 行。
- **BREAKING**：无。5 个符号零消费，删除后运行时行为、API、路由、DB、前端均不变。
- **不动**：`.env`（被 `.gitignore:70` 忽略，属本地环境配置；其中 `AGENTSCOPE_PORT`/`SCREENSHOT_INTERVAL` 两键将不再被读取，仅登记）· `data/agentscope_workspaces` 目录与其中数据（保留）· `DEVICE_SERIAL`（`tools/dump_ui.py` 在用）与 `SERVER_PORT`（`run.py` + vite proxy 在用）。

## 关联文档

- 依据：本会话 D0 层代码检测（问题项 D0-1~4）
- `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md` §七「关键开关（环境变量）」（本次同步其中一行）
- `dev_docs/05-开发与测试/设计方案与报告/设计方案-Django设计系统分层.html`（D0 层定义：只做进程装配 / 路由总表 / 外部资源根 / 插槽开关）
- 范围外登记（本次不修）：`ARCH-00:620` 的 `DEVICE_ENGINE airtest_u2（默认）` 与代码默认 `u2` 不符（`engines/device/registry.py` 只有 `u2`）；`ARCH-00:533/:621` 的 `DEVICE_SESSION_ENABLED` 全仓代码 0 命中（幽灵开关）
- 说明：`dev_docs/文档编号对照表.md` 不存在，故不引用编号文档

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无；纯删除零消费配置，`.openspec.yaml` 已声明 `skip_specs: true`）

## Impact

- **删除**：`config/agentscope_config.py`（62 行）
- **修改**：`config/settings.py`（删 2 个块，约 −13 行）· `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（−1 行）
- **不影响**：运行时行为、`apps/`、API 契约、路由表、DB、前端、`openspec/specs/`
- **测试范围**：`python manage.py check` · `ruff check config/` · `gen_arch_stats.py --check-boundaries` · 相关单测/集成测
