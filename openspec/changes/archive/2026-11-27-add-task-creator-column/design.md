## Context

- `task_tasks.created_by` 自 `task_list/migrations/0005_task_created_by` 起存在（`CharField(max_length=64)`，默认空串），写入点是 `backend/apps/task_list/views.py` 的两条提交分支（`_submit_material_workflow` / `_submit_assistant_sop`），值取 `str(request.user_id)`；`request.user_id` 由 `backend/gateway/middleware.py` 从 JWT `sub` 注入，即 Django 内置用户表主键的字符串形式。
- 列表读路径：`AgentTaskListAPIView.get` → `Task.objects.only(*api.TASK_LIST_FIELDS)` → `api.serialize_agent_task_row`。`TASK_LIST_FIELDS` 不含 `created_by`，`.only()` 缺席字段一旦被访问会逐行补查（N+1）。
- 前端 `frontend/src/modules/task-list/components/TaskBoard.vue` 用 `COLUMNS` 常量声明表格列，单元格走 `#cell-<dataIndex>` 插槽；行类型 `TaskRecord` 在 `frontend/src/shared/types/ai.ts`。
- `backend/shared/users.py` 已有 `resolve_username(user_id)`：单行查询，查不到时回落成 id 字符串；全仓无调用方，且已被登记进退役清单（`openspec/cancelled/retire-backend-dead-code`）。

## Goals / Non-Goals

**Goals:**

- 任务清单每一行都能看出提交人账号名（admin / Kahoku 这类登录账号名）。
- 历史任务不改数据即可显示；账号改名后历史行跟随当前账号名。
- 解析失败（提交人为空、账号已注销、值不是用户主键）时该行降级为「—」，不影响该行其它字段与操作。

**Non-Goals:**

- 不改任务详情接口（`GET /api/tasks/{id}/`）、报告页与报告台账的字段。
- 不加按创建人筛选 / 排序 / 导出，不加「创建人」的写操作。
- 不改提交写入口径（仍写用户 id），不做数据迁移，不复活或修改 `resolve_username`。
- 不动 `Task.created_by` 的列定义与既有 `rerun_task` 复制提交人的口径。

## Decisions

**D1：读取时批量解析，新增 `shared.users.usernames_by_id(ids) -> dict[str, str]`。**
列表一次 `filter(pk__in=[...])` 取回账号名，序列化时查字典。理由：一页最多 100 行，逐行查是典型的 N+1；`resolve_username` 的回落语义与「显示 —」冲突（它会把查不到的 id 原样返回），且它在退役清单里，不复用。
备选：① 逐行 `resolve_username` —— N+1 且语义错；② 新建任务时把账号名落库 —— 账号改名后历史记录不跟随，与规格「账号改名后历史行跟随当前账号名」冲突；③ 在 `task_list/api.py` 里直接 `get_user_model()` —— 能用，但 `shared/users.py` 已经是「User 查询」的既定归宿（`is_superuser` / `is_operator` 都在此），放这里避免各 app 各写一遍。

**D2：行契约新增两个只读字段，展示派生留给前端。**
`created_by`：提交人标识原样（空串表示未记录）；`created_by_name`：解析出的账号名，解析不到为空串。前端 `created_by_name || "—"`。理由：后端只给事实、前端做展示派生是本仓既有口径（`case_label` / `case_rows`、`report_run` 皆然）；保留原样字段便于排障时把界面对上数据库行。备选：只下发 `created_by_name` 并把「—」写进后端 —— 展示文案就散到后端，且原样字段丢失排障价值。

**D3：`TASK_LIST_FIELDS` 必须补 `created_by`。**
否则 `.only()` 未加载该列，序列化访问时每行补查一次，与 D1 的批量查询叠加成 1 + N 次查询。

**D4：列位放在「创建」（创建时间）左侧。**
「谁建的 / 什么时候建的」相邻，扫读时同一段信息一起读；`minWidth: 110`、`align: center`，沿用既有列声明形态，不新增样式类。表格总宽由 Element Plus 在容器不足时横向滚动承担，无需改表格组件。

**D5：解析范围与降级。**
`created_by` 为空或不是纯数字 → 不参与批量查询，`created_by_name` 为空串 → 前端显示「—」；账号已注销（查不到行）同理。批量解析异常时按空字典处理，列表其余字段照常返回（列表接口不因追责字段失败）。

**D6：创建人做成渐变标签，复用状态胶囊的渐变配方但不复用其圆角。**
标签 = 同色系两档 `color-mix` 渐变底（`26%` → `8%` 笔色混卡片底）+ 半透明笔色描边 + 8px 同色圆点 + 账号名文本。圆角取 `--app-radius-sm`（`4px 8px`，Tag/按钮档），与同行「执行状态」胶囊的 `--app-radius-pill`（`4px 10px 6px 8px`）区分开，避免两种语义看起来是同一个零件。描边取 `color-mix(笔色 70%, 墨色)`，让 `--c-runner` 这类浅笔也有轮廓。
备选：① 直接复用 `.status-pill` 样式 —— 语义混在一起，状态与人的标签会分不清；② 新建全局 Tag 组件 —— `shared/components` 现有 19 个零件里没有 Tag，为一个列新建公共件属于过度抽象，且会引出「第二套皮肤」问题；③ 纯色块无圆点 —— 只靠底色区分，浅笔对比度不够。

**D7：颜色映射 = 账号名 FNV-1a 哈希取模 9 支彩笔，大小写与首尾空白先归一。**
色池取 `--c-dashboard` / `--c-device` / `--c-element` / `--c-case` / `--c-runner` / `--c-report` / `--c-ai` / `--c-workflow` / `--c-ops`；**排除** `--c-task` 与 `--c-account`——技能口径里这两支只服务侧栏入口，不扩散到页面。归一（`trim().toLowerCase()`）保证 `kahoku` / `Kahoku` / ` kahoku ` 同色。
备选：① 按用户表顺序分配 —— 新账号加入或删号会让所有人换色，不可接受；② 直接算 HSL 色相（`hsl(hash%360 ...)`）—— 能保证几乎不撞色，但要写颜色字面量、绕开调色板与门禁（硬规则：颜色一律取令牌）；③ 后端下发颜色 —— 颜色是纯展示派生，且会新增接口字段与「谁定色」的口径，收益不抵成本。
碰撞容忍：9 选 1，两个账号仍可能同色；此时文字与圆点仍在，识别以账号名为准。要绝对不撞色就得扩大色池或引入组合色（双色描边），留待有真实反馈再评估。

**D8：不是卡片的重复皮肤，不新增令牌。**
`.creator-tag` 只存在于任务清单表格单元格内（与既有 `.status-pill` 同级），样式落在 `TaskBoard.vue` 的 scoped 样式里，哈希与色池下沉到 `helpers/task-card.ts` 纯函数（组件只渲染）。全程引用既有令牌，`npm run lint:styles` 的令牌/几何门禁继续把关。

## 模块防火墙自检

- **跨 App import**：`task_list` 只新增对 `backend.shared.users`（通用能力，非 app）的调用，未 import `accounts` 的 views/service/内部实现；`accounts` 也没有账号名查询接口，无需新增跨 App 边。
- **写库路径**：本变更零写库，所有改动在读路径（`.only()` 白名单 + 序列化 + 前端展示），不经 `api.py` 新增写函数。
- **Model 只读**：新增的 User 查询在 `shared/users.py`，与既有 `is_superuser` / `is_operator` 同源，不新增跨 App 内部依赖。
- **前端不直连数据库**：前端只消费 `GET /api/tasks/` 下发的新字段。

## Risks / Trade-offs

- [列表多一列，窄屏更挤] → 列宽取既有 `minWidth` 档位（110），表格由 Element Plus 横向滚动兜底；不在本单引入列显隐或列配置。
- [账号已注销 / 历史脏值导致界面出现 id 或空白] → 解析失败统一空串 + 前端「—」，并在灰盒用例里覆盖「空提交人」与「非数字提交人」两种降级。
- [批量查询随页大小增长] → 一页 100 行上限，单次 `pk__in` 查询；不引入缓存，避免账号改名后读到旧名。
- [账号改名后历史行显示新名（信息漂移）] → 这是规格选定的口径（读取时解析），排障需要冻结名称时可另开变更落快照，本单不做。
- [9 支彩笔仍会撞色] → 标签内始终保留账号名文本与圆点，识别以文字为准；真出现「两个高频账号同色」的反馈再扩色池或改双色描边。
- [浅色笔（`--c-runner`）在暖白纸面上不够醒目] → 描边混墨色（`70% 笔色 + 墨色`）保证轮廓，渐变底取 26% 起，文字统一墨色。
- [长账号名把列撑开] → 标签设 `max-width: 100%`，名称文本省略 + `title` 悬浮全文，列宽仍由 `minWidth` 控制。

## Migration Plan

1. 先发后端：列表行多两个字段，旧前端忽略未知字段，无影响。
2. 再发前端：新增列读 `created_by_name`。
3. 无数据库迁移、无数据回填；回退＝回退前后端两处改动，库里不留任何新字段或快照。
