## Why

「模型读日志」目前只读平台**内存缓冲**：`read_device_log` 走 `LogBus.read_range`，而缓冲只保留 `DEVICE_LOG_BUFFER_SECONDS`（默认 10 分钟）与上限行数。于是模型查一个稍早的时刻会得到「该时间范围内无日志（也可能已超出缓冲保留时长）」—— 实测就是这样：设备明明在 `11:47:04.687` 打了 `switch_on`，但 12 分钟后模型再查就查不到。平台其实已经把日志**落盘**（`device-log-file-archive`），只是没人从那里读。

同时，验收模型当前的工具子集只有截图工具，无法自己核对日志（只有平台喂给它的证据）。

## What Changes

- 日志时间范围查询的数据源由「仅内存缓冲」改为「**内存缓冲 ∪ 已落盘的日志文件**」：缓冲覆盖不到的时刻从 `logs/{SKU}_{端口}.log` 按时间范围回溯读取，两路结果按（时间戳、来源、原文）去重合并；查询结果不再受缓冲保留时长与缓冲上限行数限制。**BREAKING**：无（只在缓冲没数据时多读一处；缓冲命中行为不变）。
- 模型可自查 10 分钟以前的日志；`read_device_log` 的返回额外给出本次各来源的行数（缓冲 / 文件），便于排查「为什么以前查不到」。
- 只读边界不变：MUST NOT 连设备、MUST NOT 建新连接、MUST NOT 打开或改变任何端口的监听开关、MUST NOT 写库。
- 将该只读日志工具**装配进验收模型**（此前只有执行模型有），使验收侧可自行核对日志；**BREAKING**：改变 `VERIFIER_TOOLS`（原为仅 `screenshot_page`），既有规格里「装配 MUST NOT 改变验收模型的工具子集」与「verifier 仍仅为 `screenshot_page`」随之修正。
- 验收模型的系统提示词补一条自查指引（可调用该只读工具、按时间点/跨度/端口/关键词查询、不要臆造日志），随可逆迁移下发到存量库。
- 非目标：不改验收模型「由平台喂日志证据」这条链路（上一变更已定，继续作为兜底）；不改生产步骤的 5 秒取证窗与命中等级口径；不改端口监听开关的归属（仍归用户）。

## 关联文档

- PRD-08（AI 助手 · 设备操控 · 工具箱）。
- 依赖既有能力：`device-log-file-archive`（日志文件与行格式）、`device-log-capture`（缓冲与采集）、`device-log-read-tool`（被修改的工具契约）、`device-log-evidence`（证据口径不变）。
- 与 `ai-device-planner-tools` / `ai-model-debug` 的关系：这两份规格里写着「verifier 仍仅为 `screenshot_page`」「验收模型为截图校验工具」，本变更把口径改为「截图 + 只读日志工具」。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `device-log-read-tool`: 「只读日志查询工具可被调用」的数据源由仅缓冲改为缓冲 + 已落盘文件；「工具装配进执行模型」改为装配进执行模型**与验收模型**；新增「缓冲之外从日志文件回溯」的要求（范围切窗、去重合并、行数上限、文件缺失时的如实口径）。
- `ai-device-planner-tools`: 「planner 装配页面流工具子集」的场景「其它角色子集不受影响」里，验收模型不再是「仅 `screenshot_page`」。
- `ai-model-debug`: 「调试页展示该角色实际生效的配置」里对验收模型工具清单的描述同步为「截图 + 只读日志工具」。

## Impact

- 引擎：`engines/device/logfiles.py`（新增按时间范围回读与时间戳解析）、`engines/device/logbus.py`（`read_range` 合并缓冲与文件）、`engines/ai/agentscope/config.py`（`VERIFIER_TOOLS`）、`engines/ai/skills/platform-tools-manual/SKILL.md`（链路归属里的验收模型工具清单）。
- 后端：`apps/ai_assistant/tools.py`（`read_device_log` 的说明与返回里的来源行数）、新增可逆迁移同步 `ai_agents.prompt_verifier` 的自查指引。
- 测试：`tests/graybox/unit/`（按范围回读、缓冲缺失时回溯文件、验收模型工具子集、提示词迁移）。
- 兼容性：模型查最近时段的行为不变（缓冲优先）；`VERIFIER_TOOLS` 变化会让调试页的验收工具清单多一行（与实现一致）。
