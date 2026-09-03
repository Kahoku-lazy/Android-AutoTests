# Frontend AGENTS.md — AI 约束

> 工作于 `frontend/` 时必须遵守 前端只显示状态，读写数据，不执行逻辑。


---

## 0. 动手前

1. 需求模糊 → 列 3～5 种理解让用户选，禁止默默挑一种执行。
2. 先读目标 `.vue` 的 **template + script + style 三块**；改 CSS 前提取全部 class，禁止凭印象重写漏 inner class。
3. 编写细则与决策树 → `.agents/skills/android-autotests-rules/references/frontend.md`；关单自检 → skill `vue-frontend-check`。
4. **同步约定**：全局事项（后端 WS 事件表、响应信封、共享组件清单、端口/协议、分层纪律）变更时，必须同步 `.agents/skills/android-autotests-rules/references/frontend.md` 与 skill `vue-frontend-check`（checklist/calibration 对应口径）。
5. **模块专属约束**（红线/契约/协议特例/关单附加项）唯一落点为 `src/modules/{name}/AGENTS.md`，变更只改对应模块文件。
6. **包管理器（硬约束）**：`frontend/` 用 **npm**（存在 `package-lock.json`），**禁用 pnpm**——误用 pnpm 会把 npm 已装的依赖迁到 `node_modules/.ignored` 并触发重装，破坏依赖/正在运行的 dev server。前端命令一律 `npm install` / `npm run dev` / `npm run typecheck` / `npm run build:check` 等。

---

## 1. 职责与红线

### 1.1 分层与模块边界

| 层               | 只做                           | 严禁                    |
| --------------- | ---------------------------- | --------------------- |
| `.vue` 展示       | 渲染 / v-model / emit / testid | 任何 HTTP、复杂业务、校验编排   |
| `*.logic.ts` 编排 | 组合 composable、提交前校验、清表单      | 直连 HTTP               |
| 流程 composable   | API → 副作用 → 跳转               | 表单校验、弹校验 toast        |
| 校验 composable   | `errors` / `canSubmit`       | 发请求                   |

- 组件**必须**走模块 `api.js` / `api/*.ts`；业务 HTTP 经 **djangoClient →** `/api/...` **DRF**（唯一 HTTP 出口）。

**总体禁止（适用于任何前端代码）**：

| 禁止 | 说明 |
| --- | --- |
| 数据库直连 | 一切数据来自 REST / WS |
| 业务状态判定 | 消费后端权威 `state` 字段，禁止自行推导（`deriveTaskStatus` 已删，taskUtils 只读 `state` + `running`；禁止新增推导逻辑） |
| 设备 / 引擎直连 | 不碰 ADB / u2 / Airtest / Playwright；设备交互全经后端 API |
| AI 推理 | 经后端 HTTP API（任务发布），禁止前端调用模型 |
| 文件 I/O | 报告 / 截图 / 日志落盘全由后端完成 |
| WS 通道（硬约束） | 仅 2 消费点，路由真相源 `gateway/routing.py`（**禁止新增**）；截图流已快照化，禁止恢复 WS 截图流 |
| SSE 通道（硬约束） | 已移除（主对话删除）——禁止恢复；通道封闭集合以 `architecture.md` §一 为准 |

**模块边界与契约总表**（模块专属细节唯一落点 → `src/modules/{name}/AGENTS.md`）：

| 前端模块 | 后端 App | 通道 | 一句话提示 |
| --- | --- | --- | --- |
| dashboard | dashboard | HTTP | 全平台唯一只读区 |
| device-pool | device_pool | HTTP | 设备生命周期 UI，30s 心跳 |
| device-inspector | device_inspector + device_pool（设备列表） | HTTP（无 WS） | 快照抓取回看（REST） |
| element-locator | element_locator | HTTP | 三域资产 CRUD |
| case-manager | case_manager + device_pool/element_locator/test_runner（调试） | HTTP + **WS**（编辑锁） | 用例定义编排 |
| test-runner | test_runner + case_manager/device_pool（只读） | HTTP + **WS**（进度） | 执行看板 |
| report-generator | report_generator | HTTP（下载走 FileResponse） | 报告只读 |
| workflow | workflow + element_locator（素材） | HTTP | VueFlow 编排（Pinia 用户之一） |
| ai-assistant | ai_assistant + **evaluator（前端寄宿）** + 各业务 App（经 Tool 后端） | HTTP | 任务发布 + 多线路配置 |
| views/LoginView | accounts | HTTP | 登录/注册入口（accounts 唯一前端入口；认证经 `/api/auth/*`） |

**Pinia 现状（唯一真相）**：全前端仅 3 个 store —— workflow `wf-workflow` / `wf-library` + device-inspector `device-inspector`；均模块内使用，禁止跨模块 import；新建 store 走 `.agents/skills/android-autotests-rules/references/frontend.md` 状态管理决策树（先 ref → composable，不默认用 Pinia）。

**共享层边界（**`frontend/src/shared/`**）**：

| 单元 | 只做 | 禁止 |
| --- | --- | --- |
| `api-client.ts` + `api-auth-interceptors.ts` + `auth/token-storage.ts` | axios 实例（baseURL `/api`、120s 超时）、`DjangoResponse` 信封类型、`formatApiError` 中文文案（拦截 409/404/401/5xx）；JWT 附加、401→refresh→重放、失败跳登录 | 业务逻辑；表单校验；文案暴露技术术语 |
| `ws-url.ts` | WS URL 构造（Vite 代理） | 直连后端端口 |
| `icons/` | `makeIcon` 工厂统一生成 | 无必要的独立 `IconXxx.vue` |
| `components/` / `patterns/` | 通用展示组件（WorkbenchHeader/AppTable/AppCard/KpiCard/FilterTabs/RateBar/ErrorState/EmptyState/ConfirmButton） | 业务组件（归各模块） |
| `types/` | 跨模块 DTO 类型 | 类型与后端契约不一致 |

**视图层与路由**：`views/LoginView`（登录/注册入口、表单校验、错误提示；accounts 后端唯一前端入口，认证经 `/api/auth/*`）· `views/NotFound.vue`（404 兜底）· `router.ts`（汇总 9 模块 routes、JWT 守卫无 token→/login、`afterEach` 更新 document.title；路由只声明不做业务）。

### 1.3 契约规则

- 逻辑层接口与后端协议一致（路径、方法、字段、信封）；对照后端 `urls.py`、Serializer、`dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md`；模块级特例见各模块 `AGENTS.md`。
- JSON：前端 camelCase，HTTP snake_case；响应 `{status, data|message}`（**特例**：test-runner `/runner/*`、report-generator `/reports/*`、workflow legacy、element_locator legacy（`/elements/pages|items|web*|api-*`）、case_manager legacy（`/cases/definitions|directories|lock|...`）、evaluator legacy（`/evaluator/banks|runs|frameworks|...`）为平铺 `{status, ...}` 信封，前端按端点结构读取；`step-types` 特例 `{status, data:{types}}`）。

---

## 2. 模板 / 样式 / 布局（每次改 UI 必做）

1. **布局裁剪（P0）**：真实页面缩小窗口可滚；侧栏展开不挤爆；表格区 `flex: 1 1 0; min-height: 0; overflow-y: auto`；外层禁止乱加 `overflow:hidden`。
2. **Dialog/Drawer**：长内容可滚，底部按钮可达。
3. **展示组件**：薄组件；危险操作确认；编辑锁只读禁用；子面板只改自己 v-model 块；纯展示子组件不为「配套重构」而改（只改契约/图标/bug/a11y）。

其余验收口径（字段完整性 / 截断 / 四态 / 多视图互斥 / composable 入参 / 信封解包与保存清洗）→ skill `vue-frontend-check`；布局与组件规格 → `doodle-craft` skill；风格值一律读 `src/shared/styles/tokens.css`（先看头部「现行 / @deprecated / 待收敛」声明再取 token）。

**硬陷阱**：① CSS 块注释内禁止嵌 `*/`（列举 token 用顿号或 `、`，不要用 `/` 拼接）；② 组件 scoped 内禁硬编码色值/字号（字号 ≥12px、只用 `--app-*` token）；JS 画布例外（ECharts/Canvas/动态 SVG）用字面量，改 tokens 后同步 JS 渲染配置；③ 禁项：玻璃态（`backdrop-filter` 全局清零）、旧色值 `#4a4e69`/`#9a8c98`。

---

## 3. 协议要点

- **HTTP / DRF**：组件 emit → composable → 模块 `api` → `djangoClient` → `/api/...` DRF（唯一出口；禁止旁路直连后端端口或另起非约定 HTTP 客户端）。
- **WS**：`wsUrl('/ws/...')` 经 Vite 代理，禁止直连端口。test-runner 事件 type 不可漏（9 种：`log` / `heartbeat` / `case_started` / `step_started` / `step_result` / `iteration_result` / `case_finished` / `run_finished` / `device_error`，见 `useTaskWebSocket.ts`；后端另发 `run_started`，前端暂不消费）。编辑锁见 `src/modules/case-manager/AGENTS.md`。
- **报告下载**：FileResponse 用 `fetch().text()`，不用 JSON `api()`。
- **SSE（AI）**：已移除（主对话删除，ARCH-08 v3.4）——任务改走 HTTP 任务发布 `POST /api/ai/tasks/submit`，**禁止恢复 SSE 流**。

---

## 4. 关单前

- 跑 skill `vue-frontend-check`（详细门禁）+ 本模块 `AGENTS.md` 关单附加项。
- 非 skill 项：`diff` 每行可追溯到用户需求；真实页面验证（构建通过 ≠ 完成）。
