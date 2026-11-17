## Context

`/ai-assistant` 是占位页。运营 Agent 配置在 `AIRole`（`role_id`、名称、一条模型配置、系统提示词），接口为 `/api/ai/roles/`。`create_agent` 只接收提示词文件名，工具在创建后由调用方经 `build_adb_tools()` 挂上。平台侧装配在 `engines/backend_bridge`，现有 `session_for` 把会话放在进程内字典，刷新或重启即丢。取消令牌按任务号登记，不能直接当对话栏的键。动机见 proposal.md。

## Goals / Non-Goals

**Goals:**

- 助手名片与运营配置分离：只引用 `role_id`，展示字段单独存。
- 工具勾选可序列化，运行时经域门面过滤。
- 每个对话栏一个可恢复的轮次记录；进程内实例只服务续聊。
- 助手视觉登记为模块专有，不改全站令牌。

**Non-Goals:**

- 不实现 SOP 选择助手、不改 SOP 步骤 YAML。
- 不把 `create_agent` 改成接收数据库提示词正文。
- 不把进行中的轮次做成可在重启后续跑的任务队列。
- 不改 `/api/ai/roles/` 与任务清单引用的 `api/agents.ts`。

## Decisions

### 1. 新表 `ai_assistants`，不复用已退役的智能体表

一行存 `assistant_id`、`display_name`、`avatar`（可空 Text）、`marker`、`role_id`（普通字符串，不建外键）、`tools`（JSON）。`role_id` 不建外键，是为了运营配置被删时助手还在，对话前再校验。

备选是把这些字段塞回旧智能体表。否决：那张表的列表接口已规定不下发头像，且任务清单仍读它的客户端；混在一起会把测试助手和任务发布绑死。

### 2. 编号生成器与 `role_id` 分开

新函数按当地日期加 `_` 加大写字母与数字后缀生成，查重后写入唯一列。不改 `services/role_id.py` 的小写、无下划线格式。当日重试上限沿用 8 次，耗尽返回 503。

### 3. 头像在写入层压缩

`api.py` 用 Pillow 把上传图转成最长边 128 的 JPEG，质量从 80 往下降，直到 base64 文本不超过 12KB。列表序列化只给 `has_avatar`。`GET /api/ai/assistants/{assistant_id}/avatar/` 才返回正文。不接受前端传来的 base64 原图直存。

### 4. 工具目录放在 `ae_harness/tools`，过滤放在 `backend_bridge`

`tools` 增加只读目录函数：域、预设、函数名与说明。它不读配置、不造 Agent。`backend_bridge` 按保存的「预设 + 加入/去掉」调用 `build_adb_tools()` 或只读子集再过滤。禁止 import `tools/adb/tools.py` 的实现来绑定。

勾选 JSON 形状：`[{"domain":"adb","preset":"all"|"readonly","add":[],"remove":[]}]`。空数组表示无工具。

### 5. 运营提示词经只追加的系统提示钩子接入

`create_agent` 仍传一份最小提示词文件名。`backend_bridge` 在创建时挂一个只追加的 `on_system_prompt`，把 `AIRole.system_prompt` 接在后面。不改 `create_agent` 签名，不把数据库正文写进 `prompts/*.md`。该钩子只追加调用方传入的字符串，不读库；读库留在后端，正文作为参数传入。

### 6. 对话栏状态落库，Agent 实例留在进程

新表 `ai_assistant_threads`：`thread_id`、`assistant_id`、`snapshot`（首次发送时的 role 连接参数、提示词正文、工具勾选）、`status`（idle / running / cancelled / interrupted）。消息表 `ai_assistant_messages` 存用户句与助手最终文本。

进程内按 `thread_id` 复用 Agent。没有实例时，用该栏的 `snapshot` 重建，再把已落库的消息补进上下文，然后跑新的一句。这样刷新能续聊，且不会每句新建。

进行中的轮次在工作线程跑。页面用轮询读状态，不新开 WebSocket。取消为该 `thread_id` 登记独立的 `CancelToken`，不写入任务号字典。进程启动时把仍为 `running` 的栏标为 `interrupted`。

备选是复用 `session_for` 的内存表。否决：它不落消息，刷新即丢，无法满足离开后仍能看到结果。

### 7. 笔色与样式只在助手模块

色板写在 `frontend/src/modules/ai-assistant/tokens.css`，创建时后端按「上一张助手的 marker」取下一支不同色，不按色相彩虹序。doodle-craft 登记「AI 助手颜料片」：虚线允许颜料片与对话栏面板；笔色渐变允许无头像圆、发送钮和对话页头图标；当前栏用浅蓝填充加墨色框。不改全局 `tokens.css`。

### 8. 谁可以写

沿用运营 Agent 配置：运营或超级管理员可创建、修改、删除助手；已登录用户可读列表、取头像、开测试对话。普通用户写返回 403。

## 模块防火墙自检

- 助手的增删改只在 `backend/apps/ai_assistant/api.py`。View 只分发。
- 读 `AIRole` 留在本 App，不跨 App import service。
- `engines` 不 import `apps.*` / `django.*`。后端把连接参数、提示词正文、工具勾选作为参数传入 `backend_bridge`。
- `backend_bridge` 不 import `ae_harness.assistant`。
- 工具目录不反向依赖 `agents/`。
- 前端只经 `ai-assistant` 的 api 层访问 HTTP，不直连数据库。
- 不改计费口径。测试对话若产生用量，沿用现有用量记录形状交给既有入账路径；不新建价格表。

## Risks / Trade-offs

- [进程内实例在重启后丢失] → 消息已落库；重启把 running 标为 interrupted，用户重新发送时按 snapshot 重建。不承诺重启后续跑同一轮。
- [多进程部署时取消令牌只在本进程] → 本期与现有任务取消相同，接受单进程。不引入跨进程队列。
- [12KB 头像仍比纯色圆大] → 列表不带正文，只在卡片需要时按编号取。
- [只追加系统提示与文件提示词叠在一起] → 最小文件只放一句占位，运营正文是实际人设。占位不得包含设备操作指令。
