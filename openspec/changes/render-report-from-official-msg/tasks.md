## 1. 对齐记录的读取契约

- [x] 1.1 在 `engines/ae_harness/event/` 增加对齐记录的只读视图：按六段读取 `run` / `input` / `replies` / `observations` / `summary` / `events`，缺段或空段时返回空默认值而不是抛错；验证：用「完整记录」「只含 replies 的记录」「空记录」三份样例读取，均不抛错且返回结构完整。
- [x] 1.2 增加对齐记录的 schema 契约守护：断言记录文件带 `schema` 字段且取值为 `agentscope.run/1`，六段键齐全；验证：`python -m pytest -c tests/pytest.ini tests/arch/unit -q` 通过。

## 2. 内容块到报告区块的映射

- [x] 2.1 实现五类内容块（`thinking` / `text` / `tool_call` / `tool_result` / `hint`）到报告区块的渲染，未知块降级为通用区块；验证：用含五类块与一个未知块的样例记录渲染，断言区块数量与出现顺序与块顺序一致，未知块有标题且未丢。
- [x] 2.2 工具调用与结果按内容块身份配对成一张工具卡；结果块缺失时单独成卡并标注「结果缺失」；验证：构造「两次并发调用各有一结果」与「一次调用缺结果」两份样例，断言前者两张完整卡、后者一张带标注的卡。
- [x] 2.3 子目标分组从文本块里的阶段标记派生，标记缺失时退化为单组并标注「未分阶段」；验证：含标记与不含标记两份样例，断言分组数分别为多组与 1。
- [x] 2.4 报告用量取自消息对象的累计用量、耗时取自运行汇总；两者缺失时显示「未知」且不在渲染期重算；验证：三份样例（齐全 / 缺 usage / 缺汇总）分别断言页面数字与记录一致或为「未知」。
- [x] 2.5 媒体按记录里的 URL 读取后内嵌 HTML，超过单图体积上限时退化为「仅显示路径与尺寸」；验证：用小图与超限大图两份 `file://` 样例各渲染一次，断言前者内联、后者只显示路径。

## 3. 渲染入口与路径切换

- [x] 3.1 新增「按对齐记录渲染」的入口，旧入口保留并标注为过渡；验证：两个入口各渲染一次都能产出 HTML 文件。
- [x] 3.2 助手对话 `_reply` 与 UI 执行 `run_turn` 切到新入口；验证：跑一次真实助手对话与一次真实 UI 执行任务，打开生成的 HTML，确认思考块、工具卡、最终文本按顺序出现。
- [x] 3.3 记录中没有可渲染回复时，报告显示「无内容」状态而不是空壳分区；验证：用不含 replies 的记录渲染，断言页面出现「无内容」字样。

## 4. 回归、文档与门禁

- [x] 4.1 视觉契约回归：三层分区仍默认收起、子目标序号规则不变、字号仍只有三档、左栏仍默认三成且可拖拽；验证：现有前端规格用例 `python -m pytest -c tests/pytest.ini tests/report -q` 通过 + 人工目检清单逐项打勾。
- [x] 4.2 更新模块文档 `.agents/docs/engines/ae_harness_event/ae_harness_event_observation_and_report.md`：写明报告数据源为 `replies[].msg`、旧入口为过渡、未知块降级口径；验证：文档与实现逐字段核对，`python -m utils.check_gates --only engines-agents-style` 无新增告警。
- [ ] 4.3 关单门禁：`python run.py check` 通过；`python -m pytest -c tests/pytest.ini tests/ai_assistant tests/task tests/report -q` 通过（既有 16 项鉴权/授权失败与本变更无关，需在结果里注明）。

## 5. 全链路观测与链路视图

- [x] 5.1 观测中间件接入框架全部可观测位置：`on_reply` / `on_reasoning` / `on_acting` / `on_check_permission`（连同已有的 `on_model_call` / `on_system_prompt` / `on_compress_context`），只读透传；验证：真实跑一次助手对话与一次 UI 执行，观测段出现 `reply` / `reasoning` / `acting` / `permission` 四类记录（实测 UI 路径 5 轮：reasoning 10、model_call 5、acting 4、permission 4）。
- [x] 5.2 每轮推理附带状态快照（上下文条数、计划任务、压缩摘要长度、权限模式）；验证：观测记录里 `reasoning.state` 非空，且任务清单字段随任务存在。
- [x] 5.3 报告新增「链路」页签：按顺序渲染 system prompt 全文、实际发送的消息全量（含块顺序与截图）、压缩判定、权限判定、工具执行；验证：`python -m temps.check_chain_render <aligned.json>` 六项全 OK，UI 记录渲染出 93 条链路行。

## 6. 视觉输入排查与 payload 对账

- [x] 6.1 定位「模型说看不到图」的根因：`create_model` 给 formatter 传的是默认 `input_types=["text/plain"]`，`deepseek-flash` 的模型卡声明支持 `image/png|jpeg|gif|webp`，导致截图被格式化器丢弃并替换成「saved locally at」文字；验证：直接向官方端点发带图请求返回 200 且模型答出「纯红色」，格式化器输出里 `image_url` 为空。
- [x] 6.2 修：创建模型时按框架模型卡取 `input_types` 传给 formatter（deepseek / dashscope / openai 三条分支），卡片未声明时回落 `text/plain`；验证：`deepseek-flash` 的 formatter `input_types` 含图像类型，`deepseek-chat` 仍只有 `text/plain`。
- [x] 6.3 复跑真实 UI 任务，确认模型现在能描述画面像素（「Govee Home 图标在左上角，约 nx=0.14, ny=0.12」），不再是「我无法看到」；验证：`20261124_185602` 记录的思考文本。
- [x] 6.4 观测侧对账：每次模型调用记录框架图片数、实际发送数，通道不支持时标注「图片被通道丢弃」，并附一次探测的 payload 摘要；链路页签展示该对账与警告；验证：真实记录的 `framework_images` / `images_sent` / `images_dropped` 字段齐全且一致。

## 7. 报告重排：四页签 + 阶段视图 + 观测补全

- [x] 7.1 报告改为五个页签：报告（保留）/ 概览（run + input + 用量 + 产物路径）/ 阶段 / 事件流 / 原始记录（run/input/observations/summary 原文）；验证：`python -m temps.check_tabs <aligned.json>` 13 项全 OK。
- [x] 7.2 阶段视图按轮分组：准备卡（提示词全文、工具 schema、用户消息）→ 每轮一张卡（推理/请求/返回/压缩/权限/执行）→ 收尾卡（最终文本）；阶段边界取自 `reply` / `reasoning` 观测，不再依赖文本里的 `### 目标`；验证：真实记录渲染出全部轮次卡，每卡带上下文条数与工具次数。
- [x] 7.3 角色头改成卡片样式：`role-card` 带边框/阴影/悬停反馈，折叠箭头随 `aria-expanded` 旋转 90°，展开状态一眼可辨；验证：渲染结果含 `role-card` 类，CSS 含 `[aria-expanded="true"] .caret` 旋转规则。
- [x] 7.4 事件流页增量事件默认折叠并显示计数：非 delta 事件照常列出，末尾一个「增量事件 N 条（默认折叠）」可一次展开；验证：真实记录 652 事件中 587 条 delta 被折叠、65 条常显。
- [x] 7.5 观测补全：全部观测带 `reply_id`；推理快照补 `session_id` / 压缩摘要正文 / 任务全字段 / 权限规则计数；`acting` 补 `tool_call_id` 与输出摘要；`permission` 补被判定调用的入参与 `tool_call_id`；`reply` 补输入条数/角色/结构化输出开关；`model_call_return` 补 `usage`；验证：真实运行 145/145 条观测带 `reply_id`，快照含 8 个字段。
- [x] 7.6 复跑真实任务（打开 APP → 我的 → 头像 → 登录页）：41.56 s、16 轮、15 次工具，停 `LoginActivity`；验证：设备 `mCurrentFocus` 为 `com.govee.home/...LoginActivity`，报告五页签齐全。

## 8. 设备序列号由平台传入并在执行前校验

- [x] 8.1 序列号改为平台必传：`run_ui_task(serial=...)` 去默认值，`open_session` 不再接受空串或自动探测；测试脚本改为必须从命令行/环境传入，删除 `adb devices` 猜测逻辑；验证：不传序列号时直接报错，不再有“取第一台在线设备”的路径。
- [x] 8.2 执行前校验设备：校验 adb 可用、序列号存在、状态为 `device`；未连接/离线/未授权分别给出可读错误，且在任何模型调用之前失败；验证：传入 `FAKE-SERIAL-123` 时立即抛 `平台指定的设备 FAKE-SERIAL-123 未连接；当前连接：R5CT62RH88F`。
- [x] 8.3 禁止模型自选设备：UI 执行角色不再挂 `adb_devices`（工具数 16 → 15）；工具层加序列号锁，模型传其他设备时直接拒绝；验证：锁定期 `resolve_serial('OTHER-DEVICE')` 抛 `设备由平台指定为 R5CT62RH88F，禁止改用其他设备`。
- [x] 8.4 复跑验证：平台传 `R5CT62RH88F`、无 `adb_devices` 工具、95.05 s / 27 轮，最终停在 `LoginActivity`；验证：记录 `input.tool_schemas` 15 个且不含 `adb_devices`，`user_message` 首行为平台注入的序列号。
- [x] 8.5 平台注入「设备已锁定」提示：用户消息里在序列号后追加一句「设备已由平台指定并锁定……不需要枚举或切换设备」，降低模型无谓探索；验证：同一任务复跑 27 轮 → **15 轮**、95.05 s → **44.72 s**、输入 token 439k → 172k，仍停在 `LoginActivity`。

## 9. 成本优化：运行时参数、图片尺寸与报告成本视图

- [x] 9.1 报告成本视图：轮次卡显示 `in/out token` 与缓存命中数；概览显示缓存命中率、未命中输入、末轮保留图片数；重复截图在阶段里标注「与前面某张截图完全相同」；验证：渲染 `20261125_104417` 记录，阶段卡头部出现 token 段，概览出现命中率。
- [x] 9.2 运行时参数在会话侧设置（不改 `create_agent`）：`ContextConfig(max_image_num=2, tool_result_limit=20000)`、`ReActConfig(max_iters=20)`；验证：真实跑 16 轮，`framework_images` 从第 5 轮起稳定在 2（原默认 5）。
- [x] 9.3 截图尺寸下调：`_SEND_LONG_SIDE` 1568 → 1024、`_GRID_LONG_SIDE` 2048 → 1024；验证：媒体图长边 945×2048 → 1024 级，单图输入 token 明显下降。
- [x] 9.4 优化前后同任务对比：44.72 s / 172,670 输入 / 4,014 输出 → **34.52 s / 127,975 输入 / 2,343 输出**（−23% / −26% / −42%），仍停在 `LoginActivity`；验证：两次运行设备焦点一致、工具全 success。
- [x] 9.5 截图复用提示（只改注入文案，不动工具）：新增「点击后截一张图即可；同一画面直接复用；画面可能变化时必须重新截图」；验证：同任务网格 4 → 3 次、轮次 16 → 15、耗时 34.52 s → **30.62 s**、输入 128.0k → 118.3k，仍停在 `LoginActivity`。






