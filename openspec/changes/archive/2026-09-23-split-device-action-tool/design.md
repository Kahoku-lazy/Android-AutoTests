## Context

- 现状：`apps/ai_assistant/tools.py` 的 `device_action` 用连续 `if/elif` 承接 8 个动作（start_app/stop_app/click/long_click/swipe/back/input_text/current），签名带 9 个可选参数；工具名未表达动作语义，schema 会把全部参数一并展示。
- 只读与放行机制：`engines/ai/agentscope/tool_wrapper.py::check_permissions` 对 `is_read_only` 直接 `ALLOW`（"只读工具直接放行"），否则看 `auto_allow`，再否则 `ASK`。`AUTO_ALLOW_TOOLS` 是"平台内部锁"的自动放行位。
- 工具名派生面：`TOOLS`（工具名→函数+只读）、`TOOL_META`（工具名→分类/module/action，`resolve_by_module_action` 取**首个**匹配故 action 必须唯一）、`DEBUG_PARAM_OPTIONS`（调试页 serial 候选）、`VISION_TOOLS`（executor 子集）。
- 提示词是 DB 数据：`ai_agents.prompt_executor` 含两处 `device_action(...)` 字面引用（swipe / input_text），种子在迁移 `0038`；已在 `0039` 建立"短语级条件替换 + 可逆"的先例。
- 文档与测试引用：手册 `platform-tools-manual/SKILL.md`（表格/链路归属/推荐序列/关键入参/写操作铁律 共 5 处）、主 spec `ai-platform-tool-debug`（3 条要求）、接口文档（示例与候选口径）、前端 `constants.ts` 与模块 `AGENTS.md`、前后端测试各 2~3 处。
- 计数：设备管理现有 8 个（`list_devices`/`list_apps`/`acquire_device`/`release_device`/`device_action`/`click_ratio`/`drag_ratio`/`xpath_action`）；删 1 加 6 后为 **13**，平台工具总数 **12 → 17**。
- 动机见 proposal.md - Why；条款见 specs/ai-platform-tool-debug。

## Goals / Non-Goals

**Goals:**

- 每个工具只承担一类动作，工具名直述动作语义，schema 只出现该动作真正需要的参数。
- 拆分后能力与拆分前**等价**（`input_text` 保留、`press_key` 只按 back），除 `current_app` 的只读化这一处刻意改进。
- 全仓（代码/手册/spec/DB 提示词/测试/文档）无 `device_action` 残留。

**Non-Goals:**

- 不新增设备能力（不把 `press_key` 泛化为任意键、不新增手势/多指）。
- 不动 `click_ratio` / `drag_ratio` / `xpath_action`（本就单一职责）。
- 不改工具箱分类定义、设备可见性规则、`AIPlatformTool` 表结构。
- 不改前端调试页组件逻辑（它按 schema 数据驱动，工具拆细后自动呈现新表单）。

## Decisions

**D1 拆成 6 个工具，`input_text` 独立。** 用户确认：`input_text` 不在最初列的 5 组内，但它是实盘在用的能力（执行提示词与手册都指示用它输入），删除会丢能力。独立成工具语义最清晰。

**D2 `press_key` 仅按 BACK。** 引擎 `press_key(key)` 支持任意键，但本次是"拆解"而非"扩能"，只迁移原有 `back`。工具名保留前向性：日后要泛化只需加 `key` 参数，不改变名。

**D3 `current_app` 改为 `read_only=True`。** 它只读当前前台、不动设备，与另 5 个写工具语义不同。收益：走 `check_permissions` 的只读分支免 HITL 确认，调试页任意登录用户可执行（原来作为写工具需超管）。这是本单唯一的能力面变化，已在 spec 的「只读工具任意登录用户可调用」下自然成立。

**D4 参数与守卫原样迁移，默认值最小化。** `app_control.action` 保留 `start_app`/`stop_app` 字面量（沿用提示词与手册既有措辞，避免模型重新学习）；`tap_screen.mode` 默认 `click`；`swipe_screen` 默认 `up`/`500`；`input_text.clear_first` 默认 `True`。原有守卫逐条保留：`start_app`/`stop_app` 缺 package 报错、`click`/`long_click` 缺 x/y 报错（`not x or not y`，即 0 坐标视为未提供）、未知动作报错（拆细后变为未知 mode/action 报错）。

**D5 `TOOL_META` 的 action 必须唯一。** `resolve_by_module_action(module, action)` 返回首个匹配的工具，故 6 个新工具各给独立 action（`app_control`/`tap_screen`/`swipe_screen`/`press_key`/`input_text`/`current_app`），不再共用原来的 `action`。

**D6 提示词沿用 0039 的短语级条件替换。** 替换两处：`滑动：调 device_action(serial, action="swipe", direction="up|down|left|right", distance=N)` → 用 `swipe_screen`；`输入：调 device_action(serial, action="input_text", text="要输入的文本")` → 用 `input_text`。备选：整值比对 → 仍否决（同 0039 理由：会漏掉"用户改了别处但留着这句 SOP"）。

**D7 计数与清单同步到手册与前端常量。** 手册原来就漏过 `ocr_page`（上次已补齐），本次同样要求改完后各分类条目数与标题数字一致。

**D8 按性质重组分类（4 类 → 6 类），而不是沿用继承来的归类。** 拆解时 6 个新工具默认沿用 `device_action` 的「设备管理」分类；但分类是**整类启停单位**（`views_drf.py` 按 `category` 解析工具名批量写库，工具箱每类有「全部启用/全部关闭」），13 个工具一桶会让「一键停掉所有会改手机状态的控制工具」不可达——与拆解降耦合的动机相反。故按性质重组：

| 分类 | 工具 | 判据 |
|---|---|---|
| 设备管理 | `list_devices`、`acquire_device`、`release_device` | 设备池台账，**不碰手机** |
| 设备控制 | `app_control`、`tap_screen`、`swipe_screen`、`press_key`、`input_text`、`click_ratio`、`drag_ratio`、`xpath_action` | **会在手机上产生副作用**，可整类关闭 |
| 设备信息 | `list_apps`、`current_app` | 只读，但要连设备取数 |
| 设备检查器 / 视觉识别工具 / 页面流工具 | 各 1 / 1 / 2 | 不变（页面流工具由「工作流」改名而来） |

新分类配色取 **T0 色阶值**（不发明新色）：设备控制 `#F7C948`（`--color-yellow-63`）、设备信息 `#4ECDC4`（`--color-teal-49`）；测试已要求分类色互不重复（`test_inspector_ocr_tool.py`），两者与既有 4 色均不撞。备选：只摘出「设备控制」（5 类）→ 未采用，设备信息与台账放一起仍会让「只读工具」与「占用记账」混类。**发现但不在本单修**：现有「工作流」的 `#38BDF8` 并非 T0 色（`--color-cyan-74` 是 `#89cff0`），属既有硬编码漂移，改它会影响既有分类外观，留作观察项。

## 模块防火墙自检

- **跨 App import**：新工具继续只经 `apps.device_pool.api::use_device` 与 `engines.device.registry::open_engine/close_engine`，与拆分前完全一致；未新增跨模块依赖。
- **写操作收敛**：无新增写库；数据迁移只更新 `ai_assistant` 自有表 `ai_agents`。
- **引擎边界**：上层仍只调契约方法（`start_app`/`stop_app`/`click`/`long_click`/`swipe_direction`/`press_key`/`input_text`/`app_current`），未触碰裸句柄。
- **前端 HTTP 出口**：仅改常量名清单，不新增调用。
- **数据库**：无 schema 变更；一个可逆数据迁移。

## Risks / Trade-offs

- [拆细后模型在多个近似工具间选错] → 工具名直述动作；docstring 保留原措辞与 `Args` 说明；手册第 54 行的推荐序列重写为新工具名，并保留"点击优先 xpath_action，否则 click_ratio"的既有优先级。
- [历史会话/旧提示词仍调 `device_action`] → 提示词与手册同单同步；`device_action` 调用返回 404（可读错误），不会静默走错分支。
- [数据迁移覆盖用户编辑] → 短语级条件替换 + reverse。
- [`current_app` 只读化让非超管也能执行] → 有意为之（不动设备）；已在 spec 只读工具条款下成立。
- [参数守卫迁移遗漏导致能力悄悄变化] → tasks 要求逐条对照原 8 分支，并为每个新工具补 schema/注册断言。
- [手册与常量清单再次漏项] → tasks 要求 grep 校验计数自洽。

## Migration Plan

- 顺序：先拆工具与注册表 → 引擎子集 → 提示词（种子 + 0040）→ 手册/常量/文档 → 测试与 spec → 门禁与真机抽验。
- 迁移：`0040` forward 替换两处短语，reverse 还原。无 schema 变更。
- 回滚：代码回退 + `migrate ai_assistant 0039` 即可。

## Open Questions

- `press_key` 日后是否泛化为 `key` 参数（本单只按 back）？
- `click_ratio` / `drag_ratio` 的归一化坐标操作是否终有一天并入 `tap_screen`/`swipe_screen`（本单不动，二者本就单一职责）？
