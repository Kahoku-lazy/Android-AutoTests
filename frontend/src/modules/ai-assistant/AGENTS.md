# ai-assistant 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件（本文件只写增量）。

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。

## UI 布局

- 入口 `/ai-assistant/agents`（`index.vue`）；`viewMode` 由路由驱动（`agents` / `toolbox` / `knowledge`），三子项共用 `index.vue`。评测中心已下线。
- `agents` 视图 = 纵向两个区块：
  1. **小助手看板** `.duty-section` → `AgentRouteCard` × 1（`device_control`）：身份卡 = **左正方形头像**（边长 = 右三行自然总高）+ **右三行**（名称 / `职责：UI自动化` / 助手状态）+ **底栏**「校验」「配置」（仅超管）。无独立功能标题带。每条线路独立 `route_configs.{route}.name/avatar`；第三行连通徽标**仅三种业务态**：
     - `ready` → 「已连通，可执行任务」
     - `unusable` → 「秘钥已连接，但无法使用」
     - `offline` → 「连接失败，小助手断线」
     探测进行中显示「校验中…」（过程态，非业务态）。**禁止**「未检测 / 已连通 / 已断开」。
     校验写入 `route_configs.{route}.health.status` + `results`（手动立即落库；`GET /ai/agents/health` 每 30 分钟复检；缺 `status` 的旧缓存视为过期并实探）。进页即探测，完成后徽标必为三态之一。
     探测语义：先证密钥可达（list），再对三角色发极短 chat；仅 chat 成功才算可用于执行；`is_connected`/`connected` 仅 `ready` 为 true。
  2. **任务卡片列表** `TaskBoard` → `FilterTabs` + 「新建任务」+ 调试「清空」（`POST /ai/agent-tasks/clear`）+ 按状态 `el-collapse` 分组 + 卡片字段：标题 / 状态 / 创建时间 / 设备 / **助手名**（`assistant_name`，实时取当前线路 `route_configs.device_control.name`，改名后列表刷新即同步，不固化在任务行）/ **费用**（列表行 `deepseek_cost`，与详情同一计价）/ **耗时**（`started_at`→`finished_at`，缺一则为 —）/ 「详情」。**失败卡**额外「重新执行」→ `POST /ai/agent-tasks/{id}/rerun`（克隆新建 pending，原失败记录不动）。「详情」跳转 `/ai-assistant/tasks/:taskId`。运行中按步写入 `result`；详情未终态时轮询。
- `toolbox` 视图 = **装配台**（`ToolboxPanel`）：上区「助手此刻可用」生效芯片（总闸 AND 目录启用）；下区左三源（平台业务 / 自定义 Skill / **设备提示词**）+ 右目录。业务与 Skill 源行有「交给助手」总闸；**设备提示词无总闸**，始终注入运行时。右侧选中「设备提示词」时展示规划 / 执行 / 验收三份 Markdown（`renderSkillMarkdown`）；超管可编辑并一次保存（`GET/POST /api/ai/device-prompts*`）。自定义 Skill 目录 = `engines/ai/skills`（本地仓库 + 上传）。点击 Skill 卡片进入 `/ai-assistant/toolbox/skills/:name`（左目录 / 右内容，Markdown 渲染）。平台业务每张工具卡（含已停用）有「调试」→ `/ai-assistant/toolbox/tools/:toolName`（入参表单 + 真实调用；只读登录可执行，写工具仅超管且二次确认；`GET/POST /api/ai/platform-tools/{name}*`，禁止走 `/api/ai/tools/` 内部网关）。**设备管理下真正操作手机的工具（list_apps / input_text / tap_screen / swipe_screen / press_key / current_app / click_ratio / drag_ratio / xpath_action）的 `serial` 是候选下拉**：候选 = 对请求者可见 + 在线 + 未被占用，随 schema 的 `options` 下发（无候选时给提示但仍可手输）；acquire_device / release_device 是设备池占用记账、不提供候选。业务模块默认折叠。

## 组件设计


## API 接口


## 快速验证清单
