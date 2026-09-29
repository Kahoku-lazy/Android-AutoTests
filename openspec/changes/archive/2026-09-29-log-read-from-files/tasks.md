## 1. 引擎：按时间范围回读日志文件

- [x] 1.1 `engines/device/logfiles.py`：把 `BEIJING_TZ` / `STAMP_FORMAT` 收敛到本模块，新增 `line_epoch(stamp)` 与 `range_lines(path, start_epoch, end_epoch, limit)`（尾部倒读、遇到早于起点的行即停、返回原始顺序、行数上限）。验证：新增 `tests/graybox/unit/test_device_log_file_range.py` 断言「按范围切片只返回范围内行且保持顺序」「起点早于文件最早行时如实返回空」「超过上限时最多返回上限行数」「时间戳解析失败的行被跳过」全绿；`python -m ruff check engines/device` 通过。验证结果：6 项通过（含缺失文件返回空、上限保留最新一侧）；`ruff` 通过。
- [x] 1.2 `engines/device/logbus.py` 的 `read_range`：改为「内存缓冲 ∪ 该端口的日志文件」按（时间戳、来源、原文）去重后按时间升序返回，并回报 `buffer_lines` / `file_lines`；文件定位用来源登记 + `log_dir`；`BEIJING_TZ` / `STAMP_FORMAT` 改为从 `logfiles` 导入（对外名不变）。验证：`python -m pytest tests/graybox/unit/test_device_log_bus.py tests/graybox/unit/test_device_log_files.py tests/graybox/unit/test_device_log_read_tool.py -q` 全绿（含新增的「缓冲缺失时从文件取到」「两路去重」两条）。验证结果：三个文件 85 项全绿（含新增 3 条：文件回溯取到、两路去重且升序、无文件时只用缓冲）；时间戳口径已收敛到 `logfiles`（`logbus.BEIJING_TZ` 等对外名保持可用）。

## 2. 工具：说明与返回同步

- [x] 2.1 `apps/ai_assistant/tools.py` 的 `read_device_log`：docstring 与 `at` 入参说明写清「可回溯已落盘日志」；返回新增取数来源行数；`no_log` 的 note 去掉「也可能已超出缓冲保留时长」的旧暗示。验证：`python -m pytest tests/graybox/unit/test_device_log_read_tool.py -q` 全绿（含断言返回里带两路行数、无日志时 note 不再提缓冲保留时长）。验证结果：32 项通过（新增 2 条：缓冲为空时从文件取到 1 行且 `sources={'buffer_lines': 0, 'file_lines': 1}`；无日志时 note 不再提缓冲保留时长）。
- [x] 真机核对（非清单项）：用真实日志文件跑一次 `read_device_log(at=2026-09-29 11:47:04.000, seconds=5, port=7005)` —— 结论 `ok`、`sources={'buffer_lines': 0, 'file_lines': 48}`，返回的合并条目里含 `[light_switch][I]: switch_on`（11:47:04.687）。即「12 分钟前的时刻」现在查得到，改动前这里是 `no_log`。

## 3. 角色装配：验收模型获得只读日志工具

- [x] 3.1 `engines/ai/agentscope/config.py` 的 `VERIFIER_TOOLS` 加入 `read_device_log`；`engines/ai/skills/platform-tools-manual/SKILL.md` 的链路归属行同步（验收模型 = 截图 + 只读日志工具）。验证：`python -m pytest tests/graybox/unit/test_ai_role_tool_subsets.py tests/graybox/unit/test_device_log_read_tool.py tests/graybox/unit/test_ai_model_debug.py -q` 全绿（两处 `VERIFIER_TOOLS == ["screenshot_page"]` 断言同步改为「含截图与日志工具」）。验证结果：全部通过；`test_ai_model_debug.py` 的「调试页工具清单 == 角色子集」自动跟随（19 项），`test_ai_platform_tool_debug.py` 的「子集 ⊆ 注册表」亦通过。

## 4. 提示词：验收模型自查指引

- [x] 4.1 新增 `apps/ai_assistant/migrations/0049_add_verifier_log_tool_guidance.py`（依赖 `0048`）：锚点取 0044 插入块的末条（「输入里没有日志证据块时，只依据截图判断…」），在其后追加「可调用只读 `read_device_log` 自查」指引（含参数、可回溯落盘日志、不要臆造、不要开端口）；不含锚点或已含该指引则跳过，reverse 精确删除。验证：`python manage.py makemigrations --check --dry-run` 无遗漏；新增单测断言「旧文 → 新文」「幂等」「已改写行不动」「回滚回到原文」全绿。验证结果：`No changes detected`；新增 `tests/graybox/unit/test_ai_verifier_log_tool_guidance.py` 4 项通过（写入位置在锚点之后、幂等、已改写不动、可逆）。
- [x] 4.2 对存量库应用并核对实际写入：`python manage.py migrate ai_assistant`，确认平台智能体的 `prompt_verifier` 含该指引且其余内容未变；若提示词已被用户改写导致跳过，如实记录。验证：迁移前后读取该行提示词的长度与关键锚点并对照。验证结果：`Applying ai_assistant.0049_add_verifier_log_tool_guidance... OK`；平台智能体（id=10）`prompt_verifier` 长度 1689 → 1856，指引出现且仅出现 1 次（`read_device_log`），五字段契约条目与 0044 锚点原文均逐字保留。

## 5. 收口

- [x] 5.1 后端关单：`python manage.py check`、`python manage.py makemigrations --check`、`python -m ruff check apps/ai_assistant engines/ai engines/device`、`python -m pytest tests/graybox/unit/test_device_log_file_range.py … -q`。验证：全部通过（不跑全量回归）。验证结果：`System check identified no issues (0 silenced)`；`No changes detected`；`ruff check` + `ruff format --check` 通过（136 文件已格式化）；九个相关用例文件共 130 项通过。
- [x] 5.2 前端关单：本变更无前端改动，仅需 `npx vue-tsc --noEmit` 与相关调试页用例仍绿（工具清单由服务端驱动）。验证：命令输出与退出码。验证结果：`vue-tsc` 退出码 0；`model-debug-log-check` 9 项 + `useModelDebug` 30 项通过（验收调试页的工具清单由接口下发，页面无需改）。
- [ ] 5.3 页面验收（用户侧，需重启后端）：到执行模型调试台发一条「查 12 分钟前那一刻的日志」，模型应能查到那条 `switch_on`（不再返回「超出缓冲保留时长」）；到验收模型调试页确认工具清单里出现只读日志工具。验证：用户目视确认。

## 6. 修订（2026-09-29，需求方澄清：验收侧不是「自己查日志」，而是「工具按规则检查」）

- [x] 6.1 新增只读工具 `check_device_log(keyword, at, seconds, port)`：模型只报关键词，平台按规则（窗口默认取平台阈值 5 秒、忽略大小写、缓冲 ∪ 已落盘文件）判定「检测到 / 未检测到」，返回时间戳、功能点、`keyword_known`、取数来源与窗口；关键词缺省 / 端口未监听 / 端口未配置 / 窗口内无日志均给可读结论。验证：新增 `tests/graybox/unit/test_device_log_check_tool.py` 8 项通过（检测到、未检测到≠出错、窗口内无日志、关键词不在表内、关键词缺省、端口未监听、端口未配置、工具箱登记为只读）。
- [x] 6.2 验收模型的工具子集由通用查询改为该规则检查工具（`VERIFIER_TOOLS = ["screenshot_page", "check_device_log"]`）；执行模型保留通用查询；工具手册的链路归属与推荐序列同步。验证：`test_ai_role_tool_subsets.py` / `test_device_log_read_tool.py` 的装配断言同步后全绿。
- [x] 6.3 验收输入附**当前关键词表**（关键词 → 功能点，取自运行时采集索引，`log_history.keyword_catalog_text()`）：经 `TaskRequest.log_keywords` 下发到引擎（`engines/ai/base.py`、`engine.py`、`workflow.py` → `VerifierRole.run(keyword_catalog=...)`），调试台由 `model_debug` 直接拼入验收对话输入。验证：`test_ai_debug_log_check.py::test_verifier_chat_input_carries_keyword_catalog_and_rule` 断言输入含 `check_device_log`、`switch_on`、两条件口径；`engine_adapter` 组装路径经 `test_ai_engine_config.py` 回归通过。
- [x] 6.4 新增迁移 `0050_verifier_log_check_contract`：把 0049 写的通用查询指引换成规则检查指引，写入「日志检测到 + 截图确认才可判 PASS」，输出字段加 `logAssertionInfo`、时间戳来源改为检查工具返回，输出格式约束与案例 JSON 改为六键；可逆、幂等、已改写行不动。验证：新增 `tests/graybox/unit/test_ai_verifier_log_check_prompt.py` 5 项通过；存量库应用后 `prompt_verifier` 长度 1856 → 2071，`read_device_log` 已被 `check_device_log` 取代、两条件与 `logAssertionInfo` 均已写入。
