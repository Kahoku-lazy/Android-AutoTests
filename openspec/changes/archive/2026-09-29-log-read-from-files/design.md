## Context

动机与实测见 `proposal.md - Why`。方案需要的现状约束（已核实）：

- `apps/ai_assistant/tools.py::read_device_log` → `LogBus.read_range` → 只读 `_ChannelBuffer.between(...)`；缓冲 `DEVICE_LOG_BUFFER_SECONDS=600`、`DEVICE_LOG_BUFFER_MAX_LINES=20000`，超出即查不到，`note` 里也写着「也可能已超出缓冲保留时长」。
- 日志文件由 `LogFileSink` 落在 `DEVICE_LOG_LOG_DIR`（默认 `logs/`），文件名与格式为 `{SKU}_{端口}.log` + `时间戳 [来源] 原文`（`logfiles.parse_log_line` 可解析）；已有 `tail_lines` 尾部读能力，但没有「按时间范围读」。
- 角色工具子集在 `engines/ai/agentscope/config.py`：`VERIFIER_TOOLS = ["screenshot_page"]`；两份既有规格写死了这个事实，改它必须同步改规格。
- 验收提示词是库中数据（`ai_agents.prompt_verifier`），已有「短语级、可逆、按锚点条件替换」的迁移先例（0039/0040/0044/0046/0047/0048）。

## Goals / Non-Goals

**Goals:**

- 模型按时间范围查日志时不再受内存缓冲限制；返回里能看出取数来源（缓冲 / 文件）。
- 验收模型能自己核对日志；平台喂证据继续作为兜底。

**Non-Goals:**

- 不改生产步骤的 5 秒取证窗与命中等级（证据链口径不动）；本变更只扩大「查询」这一路的数据源。
- 不改端口监听开关归属：仍归用户，工具 MUST NOT 因此打开端口。
- 不给规划模型加工具。

## Decisions

**决策 1：回溯能力放在引擎总线的 `read_range`，而非工具里。**

- 做法：`LogBus.read_range` 由「只读缓冲」改为「缓冲 ∪ 该端口的日志文件」，两路按（时间戳、来源、原文）去重后按时间升序返回，并额外回报两路行数。
- 理由：`read_range` 是「按范围读日志」的唯一入口（工具只是它的壳），把回溯放在这里，未来任何调用方都自动受益，且文件定位所需的信息（来源登记、`log_dir`）本来就在总线配置里。
- 备选：在工具里自己拼文件读取（工具要重复知道来源登记与目录）；改 `read_window`（那是取证链，口径不同，不该混）。

**决策 2：文件按时间范围倒读，读到范围之前即停，并设行数上限。**

- 做法：`logfiles.range_lines(path, start_epoch, end_epoch, limit)` 从文件尾部按块倒读、解析时间戳，遇到早于起点的行即停止；返回原始顺序（旧→新）；上限 `FILE_RANGE_MAX_LINES`（5000）。
- 理由：一次查询的范围通常只有几十秒，倒读能在读到范围时立刻停下，不必扫全文件；上限保护上下文与内存。
- 备选：整文件加载后过滤（大文件代价高）；只读当日归档文件（当前文件通常就够，归档留给以后）。

**决策 3：时间戳解析收敛到 `logfiles`，`logbus` 复用。**

- 做法：把 `BEIJING_TZ` / `STAMP_FORMAT` 与新的 `line_epoch` 放在 `logfiles`（它本就行格式与日期相关），`logbus` 从 `logfiles` 导入（`logbus.BEIJING_TZ` 等既有对外名保持不变）。
- 理由：两条读取路径都需要「文件行时间戳 → epoch」，各写一份必然漂移。
- 备选：在 `logfiles` 里再定义一份时区常量（重复定义，易漂移）。

**决策 4：`VERIFIER_TOOLS` 加 `read_device_log`，并同步三处口径。**

- 做法：子集加名；同步 `platform-tools-manual` 的链路归属行、`ai-device-planner-tools` 与 `ai-model-debug` 的主规格（delta 里 MODIFIED）。
- 理由：这两份规格把「验收模型仅截图工具」写成了可检查的场景，不改就会出现规格与实现矛盾。
- 备选：只改代码不改规格（规格失真，且后续变更会照着错的写）。

**决策 5：验收提示词补自查指引走可逆迁移，锚点取 0044 插入块的末条。**

- 做法：新迁移在锚点行之后追加一条「可调用只读 `read_device_log` 自查日志（含参数与「不要臆造、不要开端口」的边界）」；不含锚点则跳过，reverse 精确删除。
- 理由：与既有迁移同口径；把工具的存在与边界写进提示词，模型才会真的用它。

## 模块防火墙自检

- 引擎内改动只在 `engines/device/*`（日志读取）与 `engines/ai/agentscope/config.py`（角色子集常量）、`engines/ai/skills/` 手册文本，无新增对外依赖、无 `apps.*` import。
- `apps/ai_assistant/tools.py` 仍只经引擎公开接口取数；不写库、不碰设备。
- 迁移是唯一写库点（Django 迁移层）。
- 前端无改动（调试页工具清单由服务端 schema 驱动）。

## Risks / Trade-offs

- [文件回溯读到与缓冲重复的行] → 按（时间戳、来源、原文）去重，且缓冲行优先保留。
- [查询范围很大时读文件变慢/占用内存] → 倒读 + 到起点即停 + 行数上限 5000；超限时如实以范围内的行返回。
- [验收模型有了日志工具后不再认真看平台证据] → 平台证据仍随输入下发（上一变更），提示词里保留「以平台证据为主、可自查补充」的分工。
- [两份规格的「验收模型仅截图工具」表述残留] → 本变更的 delta 已 MODIFIED 这两处，归档时覆盖主 spec。
