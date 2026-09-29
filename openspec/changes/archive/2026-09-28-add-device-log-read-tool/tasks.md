## 1. 采集侧补端口维度

- [x] 1.1 日志行（`LogLine`）记录来源端口，采集线程写入实际监听端口，验证：单测断言同一通道混合来源的行可按端口区分
- [x] 1.2 `LogBusConfig` 增加「端口 → 通道」来源登记（默认 `7005 → H6810`，与现状一致），并在 `config/settings.py` 暴露配置项，验证：`python manage.py check` 通过，未配置时按默认登记可正常启动
  - 落地：`DEVICE_LOG_SOURCES`（JSON，可空）+ `log_evidence._source_channels()` 兜底组单条；`manage.py check` 通过
- [x] 1.3 提供「按时间窗 + 端口（或通道）读取行」的只读查询接口，未登记端口时抛可读错误并带已配置端口清单，验证：单测覆盖「已登记端口取到行」与「未登记端口报错且不返回空」
  - 落地：`LogBus.read_range()` / `channel_for_port()` / `configured_ports()` + `LogSourceUnknown`

## 2. 只读工具实现

- [x] 2.1 在 `apps/ai_assistant/tools.py` 实现 `read_device_log`（只读），支持 `at` / `seconds` / `port` / `keyword` / `serial` 入参，返回结构化 JSON（查询范围、来源、行数、行列表、命中功能点），验证：单测断言返回结构字段齐全且函数体不触碰写库与设备引擎
- [x] 2.2 实现时间点解析：支持完整时间与仅时刻（按当天），非法值报可读错误并给出期望格式，验证：单测覆盖三种输入（完整/仅时刻/非法）
- [x] 2.3 实现时间窗语义：给 `at` → **该时刻之后一个跨度**（需求方选定 B 口径）；不给 → 最近一个跨度；跨度默认 30 秒、上限 300 秒，验证：单测断言两种语义的边界与超限钳制
- [x] 2.4 实现关键词过滤与功能点还原（忽略大小写子串匹配），验证：单测覆盖「命中并带出功能点编号」与「无命中返回 0 行且说明」
- [x] 2.5 实现三种失败口径（未登记端口 / 非法时间 / 范围内无日志）的可读结论，验证：单测逐条断言结论文案要点（含已配置端口、期望格式、实际查询范围）
  - 口径修订（需求方）：**未配置端口不报错**，正常返回 `note=「端口 X 未配置为日志来源」` + `conclusion=port_not_configured` + 行数 0；提示里的端口号随传入值变化（7004 / 7003 各自成句）。单测参数化覆盖两个端口号

## 3. 工具箱与装配

- [x] 3.0 同一时刻的日志合并为一条（时间戳 + 来源相同；`text` 内保留换行；同时给出合并前原始行数）且列表**最新在上**（倒序，同一条内部保持原始先后），工具输出与验收证据两处生效，验证：单测覆盖「同毫秒三行合并成一条且含换行」「来源不同不合并」「时间戳不同不合并」「最新在上」「合并条内部不倒序」「计数口径可区分」，真机上灯空闲时段查询 `line_count == raw_line_count` 且时间戳严格倒序

- [x] 3.1 新增工具箱分类「设备日志」并把工具登记进平台工具表（`TOOLS` / `TOOL_META` / `TOOL_CATEGORIES`），验证：`list_tool_schemas()` 输出含该工具、分类正确、`read_only=true`
- [x] 3.2 把工具名加入执行模型工具子集（`VISION_TOOLS`），验收模型子集保持不变，验证：单测断言执行子集含该工具、`VERIFIER_TOOLS` 仍仅为 `screenshot_page`
- [x] 3.3 工具 docstring 写清「排查用、跨度上限、未配置端口会报错」，使 schema 摘要可读，验证：`list_tool_schemas()` 的 summary 非空且含排查口径

## 4. 验证与收口

- [x] 4.1 补齐单测覆盖 specs 每条 Scenario，验证：`pytest tests/graybox/unit -k "device_log"` 全绿（64 条：47 条既有 + 17 条本次）
- [x] 4.2 门禁与边界：`python manage.py check`、`ruff check engines/ apps/ config/`、`python tools/gen_arch_stats.py --check-boundaries` 均通过
- [x] 4.3 真机确认：后端起来（常驻采集占用 7005），通过工具网关按「指定时间点 + 端口 7005」调一次，验证：能取到灯的真实日志行并标明来源；再传未配置端口，验证返回可读错误
  - 真机结果（工具网关 `POST /api/ai/tools/log/read/`，内部令牌）：
    - 最近 20 秒 → `行数=5 结论=ok 来源端口=7005 通道=H6810`，行内容为灯真实日志（`ram free heap size: ...`）
    - `at=15:24:35.950, seconds=8` → 范围 `15:24:35.950 ~ 15:24:43.950`，3 行全部不早于 `at`（B 口径生效）
    - `port=9999` → HTTP 400「端口 9999 未配置为日志来源；当前已配置端口: [7005]」
    - `keyword=switch_off`（灯只打内存行）→ `结论=no_keyword_hit` + 可读备注
  - 工具箱数据源 `GET /api/ai/available-tools` 确认：分类数 7（新增「设备日志」），`read_device_log` 在其中、`read_only=true`、`enabled=true`
