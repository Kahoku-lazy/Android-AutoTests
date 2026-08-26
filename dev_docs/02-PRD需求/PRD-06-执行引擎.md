# PRD-06 — 执行引擎 (Test Runner)

> 关联模块：`apps/test_runner/` · 前端：`frontend/src/modules/test-runner/`
> 关联全局：[`需求大纲.md`](./需求大纲.md) §5.6（任务调度与执行中枢）
> 关联上游：[`PRD-02-设备管理`](./PRD-02-设备管理.md)（设备锁/释放）· [`PRD-05-用例管理`](./PRD-05-用例管理.md)（用例定义 steps_json）
> 关联下游：[`PRD-07-测试报告`](./PRD-07-测试报告.md)（执行结果与报告）· [`PRD-01-仪表盘`](./PRD-01-仪表盘.md)（执行统计聚合）
> 版本：v8.2 · 状态：评审中 · 日期：2026-08-21

**修订记录**

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v8.2 | 2026-08-21 | run 状态大小写收敛（TestRunRecord.status 小写，迁移 0019）；run-step 支持类型 16→25（含 9 个 adb_* 新名）；§5.3 tasks[] 补 `state`；详情页功能区 6→5；§10 补 execution_steps/ai_execution/recovery_helpers |
| v8.1 | 2026-08-19 | 补齐 F 级「职责与边界」声明（列表筛选/排队/停止/重跑/执行列表/步骤截图/缺陷记录/日志）；附录A「我不能做什么」补相邻模块边界（元素定位 PRD-04、设备检查器 PRD-03） |
| v8.0 | 2026-08-19 | 按 PRD-03 设备检查器格式重构：移除设计目录/数据流/验收汇总/实施状态/已知问题旧章节，补齐十章 + 附录A；同步代码真相（13 端点、WS 10 种消息 + seq/heartbeat、状态机 idle→queued→running→done、4 表、.js→.ts）；修正定时执行与队列恢复为已实现；登记 mode 取值漂移（now/scheduled vs immediate） |
| v7.1 | 2026-07-27 | 分层违规清零（裸 client 收敛 api.js）、跨模块 import 收敛、useExpandCollapse/useDebouncedSave 接入 |
| v7.0 | 2026-07-25 | 拍立得 KPI 卡片、双 section 布局、FilterTabs/KpiCard 接入 shared |

---

## 1. 功能定位

执行引擎是平台的**任务调度与执行中枢**：用户创建任务卡片、选择设备与用例、一键执行，通过 WebSocket 实时监控每一步进度，执行结束后自动产出可供测试报告模块消费的执行记录。

**核心职责**：

- **任务卡片**：任务卡片 CRUD（跨设备同步，非本地 localStorage），按类型（UI/API/Web）选设备与用例
- **执行调度**：设备空闲立即执行、忙碌自动排队（FIFO）、定时执行、停止/重跑/取消排队
- **实时进度**：WebSocket 推送日志 / 步骤结果 / 迭代结果，seq 递增序号 + 心跳
- **执行快照**：执行前完整快照用例步骤（selected_cases），历史可审计
- **缺陷记录**：失败步骤自动聚合生成 BUG 单

执行引擎是**管理模块（有写操作）**：任务卡片、执行记录、迭代结果均落库（`tr_` 前缀 4 表）；写库收敛于 `state_machine.py`（状态流转唯一入口）与 `api.py`（跨模块写白名单）。

---

## 2. 功能详细规格

> 本章按三个功能区域分层：任务管理（主页面）→ 执行调度 → 任务详情与实时监控。F 编号用于 §5 API 交叉引用。

### 2.1 模块一：任务管理（主页面）

**核心功能**

- **任务卡片 CRUD**：创建 / 保存 / 删除任务卡片，卡片状态由状态机统一管理
- **统计概览**：4 张 KPI 卡片展示任务状态分布
- **列表筛选**：6 Tab 状态筛选 + 搜索 + 表格 / 卡片双视图

**F-01-01 任务卡片 CRUD**

**功能实现逻辑**：用户点击「新建任务」打开弹窗，填写名称、任务类型（UI 自动化 / API 测试 / Web 自动化）、设备（仅 UI 类型必选）、用例（按类型过滤）、循环次数（1-10000）、轮间间隔（5-300 秒）、执行方式（立即 / 定时）后保存；任务卡片落库并通过 `GET /runner/tasks` 跨设备同步。

**详细功能点**：

- **表单校验**：名称必填；UI 类型必选设备；至少勾选一个用例；轮间间隔 ≥5 秒
- **保存**：`POST /runner/tasks/save` upsert（无 id 则新建，有 id 则更新）
- **删除**：`DELETE /runner/tasks/{task_id}`，仅非运行态可删
- **任务 ID**：`task_id` 为主键（如 `ID-1`）

**职责与边界**：本功能只管理任务卡片定义；执行由 F-02 调度完成，卡片状态流转由后端状态机（§4.1）唯一控制。

**验收方式**：

- 新建任务后刷新页面任务仍在（跨设备同步）
- 表单校验拦截：无名称 / UI 无设备 / 无用例 / 间隔 <5 秒均不可提交
- 运行中的任务不可删除

**F-01-02 统计概览（KPI 卡片 ×4）**

**功能实现逻辑**：页面顶部 4 张拍立得风格卡片展示任务状态分布，hover 归正放大。

**详细功能点**（前端派生口径 `deriveTaskStatus` / `taskBucket`）：

| 卡片 | 口径 |
|------|------|
| 执行中 | `running === true` |
| 等待中 | 派生状态 `queued`（`isTaskQueued`） |
| 已完成 | `outcome === 'completed'`（仅全部用例跑完归入） |
| 失败/未完成 | `outcome ∈ {stopped, interrupted, error}` 或未执行（idle） |

> 历史数据漂移兜底：`status=queued` 但 `outcome` 已终态的记录视为 `done`（前端派生时归一）。

**验收方式**：卡片数字与列表 Tab 计数一致，状态变化后实时刷新。

**F-01-03 任务列表与筛选**

**功能实现逻辑**：任务列表支持 6 Tab 状态筛选（全部 / 执行中 / 等待中 / 已完成 / 未完成 / 未执行）、名称/ID/设备搜索、表格 / 卡片双视图切换。

**详细功能点**：

- **表格视图**：10 列（任务ID / 名称 / 类型 / 设备 / 用例数 / 进度 / 成功率 / 状态 / 时间 / 操作），操作列 2×2 网格按钮：执行 / 重跑 / 报告 / 删除（非运行态）、停止（运行态）、取消排队（排队态）
- **卡片视图**：按状态 4 组展示，卡片含 ID / 名称 / 元数据 / 进度条 / 统计行 / 操作按钮
- **点击行**：跳转任务详情页 `/runner/task/{taskId}`

**职责与边界**：本功能只负责列表展示与筛选；任务状态由后端状态机（§4.1）唯一控制，前端不直接改状态字段。

**验收方式**：6 Tab 筛选正确；搜索缩小结果；双视图切换后数据一致；操作按钮按状态正确显隐。

### 2.2 模块二：执行调度

**F-02-01 一键执行**

**功能实现逻辑**：用户点击「执行」，系统按任务类型走不同管线：UI 任务校验设备并尝试获取设备锁（`runner-{serial}` 占用），设备空闲立即执行，忙碌自动入队；API / Web 任务**无需设备**，直接走统一执行管线（`API-RUN-*` / `WEB-RUN-*`）。

**详细功能点**：

- **请求口径**：`POST /runner/run` 传 `case_ids` / `loop_count`（默认 3）/ `interval_seconds`（最小 5）/ `task_type` / `device_serials[]`（支持多设备并行）/ `client_task_id` / 定时字段
- **用例加载**：按 `task_type` 从用例管理读取 enabled 用例（UI 走 `TestDefinition`、API 走 `ApiTestCase` 的 `config_json`、Web 走 `WebTestCase` 的 `steps_json`）
- **执行快照**：启动时完整复制用例步骤到 `selected_cases`，用例后续被修改不影响本次执行
- **循环执行**：`for i in range(loop_count)` 逐用例逐步骤执行，轮间间隔 `interval_seconds`
- **定时执行**：`start_at` 到点自动开始（含延迟等待）；`end_at` 到点自动停止

**职责与边界**：设备连接与锁由设备管理（PRD-02）承担（`acquire_device` / `release_device`）；本模块只调度与执行。

**验收方式**：

- UI 任务设备空闲时立即执行；忙碌时返回 `queued` 列表并自动排队
- API / Web 任务无设备可执行
- `selected_cases` 为执行时刻快照，修改用例不影响进行中任务
- 定时任务到点自动执行、自动停止

**F-02-02 智能排队（FIFO）**

**功能实现逻辑**：设备忙碌时任务进入该设备的内存队列；设备释放后按 FIFO 出队自动执行；任务卡片同步置 `queued` 状态，服务重启后可恢复（§4.4）。

**详细功能点**：

- **入队**：设备 BUSY 或跨进程占用时入队，提示「设备正忙，任务已加入队列（前面有 N 个任务）」
- **出队**：上一任务结束后 `_start_next_queued` 原子取队首（先标记占用再出队，防竞态）
- **取消**：`POST /runner/queue/cancel` 从队列移除并复位任务卡片为 `idle`

**职责与边界**：队列为进程内 FIFO + DB 任务卡片（status=queued）兜底重建（§4.4），不引入消息队列中间件；设备锁释放由设备管理（PRD-02）承担。

**验收方式**：多任务同设备按先后顺序 FIFO 执行；取消排队后设备释放不执行该任务；排队序号提示正确。

**F-02-03 停止执行**

**功能实现逻辑**：用户点击「停止」（二次确认），运行中的任务在步骤检查点自然收尾（优雅停止）；预检阶段（已锁设备尚未执行）打停止标记并在预检检查点释放设备，避免设备锁泄漏。

**职责与边界**：本功能只做协作式停止与预检停止标记，不提供强制杀进程；设备锁释放由执行管线善后处理。

**验收方式**：停止后任务 outcome 为 `stopped`、设备恢复可用；预检阶段停止不泄漏设备锁。

**F-02-04 重新执行**

**功能实现逻辑**：已终态任务可重跑——生成新执行记录，保留历史（重新执行 = 新卡片/新 run）。

**职责与边界**：重新执行只生成新执行记录，不覆盖、不迁移历史数据；历史审计与报告查看归测试报告（PRD-07）。

**验收方式**：重跑后历史记录可对比；旧 run 不被覆盖。

### 2.3 模块三：任务详情与实时监控

> 路由 `/runner/task/{taskId}` · 组件 `TaskDetail.vue`。详情页 5 个功能区自上而下：信息卡片 → 用例执行列表 → 自动化执行步骤详情 → 缺陷记录 → 执行日志。

**F-03-01 信息卡片与进度**

**功能实现逻辑**：展示任务元信息（名称/类型/设备/用例数/循环/间隔/创建时间/创建人/状态）+ 进度条 + 动态操作按钮栏。

**详细功能点**：

- **执行中额外显示**：当前执行用例名称 + 当前轮次 + 「已完成 / 总次数」
- **操作按钮按状态切换**：未执行 `[返回][执行][删除]`；执行中 `[返回][停止]`；等待中 `[返回][取消排队]`；已完成 `[返回][重新执行][查看报告][删除]`（停止 / 取消排队 / 删除均二次确认）

**验收方式**：按钮栏随状态正确切换；进度条百分比与总次数一致。

**F-03-02 用例执行列表**

**功能实现逻辑**：以可展开卡片展示每个用例的实时执行状态（展开/折叠由 `useExpandCollapse` 管理）。

**详细功能点**：

- **卡片头部**：用例 ID 标签（执行中紫色底）+ 标题 + 状态文字 + 迭代统计（🔁 总数 ✅ 通过 ❌ 失败）
- **展开内容**：迭代横幅（当前轮次 + 已完成步骤数）→ 步骤卡片列表（左侧色条：通过绿 / 失败红 / 执行中蓝 / 待执行灰，含步骤类型中文名 + 描述 + XPath）→ 性能测量区块（次数 / 平均 / 最快 / 最慢 / 中位 + 每轮明细）
- **空步骤提示**：「暂无可展示的步骤」

**职责与边界**：本功能只展示执行状态；步骤结果由 WS 推送驱动，数据持久化由执行管线（§4.2）完成，前端不落库。

**验收方式**：WS 推送驱动步骤卡片状态实时更新；性能数据存在时展示测量区块。

**F-03-03 自动化执行步骤详情（截图）**

**功能实现逻辑**：展示每个已执行步骤的截图与元信息（数据来源 `task.step_details` / 后端 `TestResult.step_details`，执行过程实时推送）。

**详细功能点**：

- Web 自动化每步自动截图，PIL 标注操作目标（红框 = 点击、蓝框 = 输入、绿框 = 断言）
- 步骤序号 + 类型（中文名）+ PASS / FAIL（失败附错误原因）
- 迭代切换查看不同轮次截图
- 组件：共享 `StepScreenshotPanel.vue`；截图经 `GET /runner/step-screenshots/{filepath}` 服务

**职责与边界**：截图由执行管线落盘（SCREENSHOT_DIR）并随 `TestResult.step_details` 记录路径；本功能仅经截图服务端点读取展示，不负责截图生成。

**验收方式**：截图标注颜色与操作类型一致；失败步骤显示错误原因；迭代切换正常。

**F-03-04 缺陷记录（BUG 单）**

**功能实现逻辑**：失败步骤自动聚合，按「用例 + 迭代 + 失败步骤序号」去重生成 BUG 编号（`BUG-001` 红色标签），默认折叠。

**详细功能点**：

- **数据来源**：`task.failedSteps`（WS `step_result` 失败自动追加）
- **每条 BUG 展示**：卡片头部（BUG 编号 + 用例标题 + 失败轮次/步骤 + 🔴 执行失败）+ BUG 元信息 + 完整步骤清单（失败步骤高亮红 + 失败原因）

**职责与边界**：BUG 单为执行会话内的失败聚合展示，不独立落库、不对接外部缺陷管理系统；失败明细持久化于任务卡片 `failed_steps`（本模块 tr_ 数据，报告模块只读消费）。

**验收方式**：同用例同步骤同轮次失败只生成一条 BUG；展开后失败原因可见。

**F-03-05 执行日志**

**功能实现逻辑**：深色主题实时日志面板，WebSocket 推送驱动。

**详细功能点**：

- 日志条目：时间戳 + 文本，按级别着色（info 默认 / error 红 / warn 橙）
- 可视高度随行数变化（最少 25 行、最多 50 行，超出面板内滚动），自动滚屏到底部
- 容量控制：上限 1000 条，超出裁剪到 500 条
- 空态：「日志将在此显示」

**职责与边界**：仅展示本次 run 的实时日志（WS 推送）；历史日志文件（log_path）归档与下载由测试报告（PRD-07）承担。

**验收方式**：日志逐行实时推送；超出容量自动裁剪；级别着色正确。

**F-03-06 单步调试（run-step）**

**功能实现逻辑**：用例编辑器（PRD-05）的「单步试运行」调用 `POST /runner/run-step`，在调试设备上执行单个步骤并返回结果与日志。

**详细功能点**：

- 支持 25 种步骤类型（`task_views.py:23-54` `KNOWN_STEP_TYPES`）：基础 UI 8 种 `click / long_click / swipe / wait / wait_disappear / sleep / verify_text / poll_text`；`adb_*` 新名 9 种 `adb_start_app / adb_kill_app / adb_perf_element_time / adb_wait_toast / adb_if_appear / adb_if_disappear / adb_loop_n / adb_loop_elements / adb_poll_text`；deprecated 旧名 8 种（历史用例兼容）`start_app / kill_app / perf_element_time / wait_toast / if_element_appear / if_element_disappear / loop_n / loop_elements`
- 可指定 `device_serial` 或使用用例编辑页顶部已选调试设备

**职责与边界**：调试设备连接由设备管理（PRD-02）提供；本功能不落库、不生成 run 记录。

**验收方式**：单步执行返回 pass/fail + 日志；未选调试设备时提示「请先在用例编辑页顶部选择调试设备」。

---

## 3. 布局与视觉设计

> 全部颜色/字号引用 Doodle Craft 主题令牌（[`frontend/AGENTS.md` §2](../../frontend/AGENTS.md)）。模块色桃粉 `--c-runner`。

### 3.1 主页面布局

```
┌─────────────────────────────────────────────────┐
│ WorkbenchHeader（标题 + 副标题）                   │
├─────────────────────────────────────────────────┤
│ ① 统计概览：KpiCard × 4（执行中/等待中/已完成/失败） │
│ ② 任务列表：搜索框 + FilterTabs(6) + 视图切换 + ＋新建 │
│    └─ 表格视图（AppTable 10 列）/ 卡片视图（4 组）    │
└─────────────────────────────────────────────────┘
```

### 3.2 任务详情页布局

```
┌──────────────────────────────────────────────┐
│ PageHeader「任务详情」+ 副标题（设备/用例数/循环）  │
├──────────────────────────────────────────────┤
│ ① 信息卡片（元信息 + 进度条 + 动态操作按钮栏）      │
│ ② 用例执行列表（可展开卡片 ×N）                   │
│ ③ 自动化执行步骤详情（StepScreenshotPanel 截图）   │
│ ④ 缺陷记录（BUG 单，默认折叠）                    │
│ ⑤ 执行日志（深色面板，自动滚屏）                  │
└──────────────────────────────────────────────┘
```

### 3.3 组件规格

| 元素 | 规格 |
|------|------|
| KPI 卡片 | 拍立得风格，微旋转排列 hover 归正放大；执行中=`--c-ai` 柔粉 ◆ / 等待中=`--c-dashboard` 柠黄 ▲ / 已完成=`--c-device` 薄荷绿 ■ / 失败=`--c-runner` 桃粉 ● |
| 表格行 | hover 淡桃粉底色（模块色 8% 透明）；操作列 2×2 网格，单按钮占满整行 |
| 状态标签 | 执行中紫 / 等待黄 / 完成绿 / 失败红（`taskStatusInfo()` 计算） |
| 步骤卡片 | 左侧色条（通过绿/失败红/执行中蓝/待执行灰） |
| 日志面板 | 深色主题，info 默认 / error 红 / warn 橙 |
| 危险操作 | 停止 / 取消排队 / 删除使用 ConfirmButton 二次确认 |

### 3.4 组件清单

| 区域 | 组件 | 说明 |
|------|------|------|
| 主页面 | `index.vue` | 页面编排（KPI + 筛选 + 双视图 + 弹窗） |
| 主页面 | `components/NewTaskDialog.vue` | 新建任务弹窗（表单 + 设备/用例选择） |
| 详情页 | `components/TaskDetail.vue` | 任务详情（5 功能区编排） |
| 共享 | `shared/components/KpiCard.vue` / `FilterTabs.vue` / `AppTable.vue` | KPI 卡片 / Tab 筛选 / 表格 |
| 共享 | `shared/components/StepScreenshotPanel.vue` | 步骤截图面板（详情页 ③） |
| 共享 | `shared/components/patterns/ConfirmButton.vue` | 二次确认按钮 |
| 逻辑 | `composables/useTaskWebSocket.ts` | WS 连接 + 消息分发 + 重连 |
| 逻辑 | `composables/taskUtils.ts` / `useDebouncedSave.ts` / `useQueuePoller.ts` | 状态判定 / 保存防抖 / 排队轮询 |

**边界状态（场景）**

| 场景 | 行为 |
|------|------|
| 任务未找到 | 详情页居中「任务未找到」+ `[← 返回任务列表]` |
| 任务加载中 | `task` 为 null 时内容区不渲染（防 null 属性访问） |
| WS 断连 | 指数退避重连（1s→2s→4s→8s→16s，最多 5 次）；`seq` 断档检测 → 触发对账重拉 |
| 15s 无心跳 | 连接丢失指示 |
| 无设备可用（UI 任务） | 执行返回 400「没有可用设备，请确认设备已连接且状态为在线」 |
| 无用例 enabled | 执行返回「no enabled test cases found」 |
| 列表空 | EmptyState 空态 |

---

## 4. 后端功能逻辑

### 4.1 任务状态机（唯一流转入口）

`state_machine.py` 是 TaskCard / TestRunRecord 状态流转的**唯一入口**，任何代码不得直接改状态字段；TaskCard + TestRunRecord 在同一事务内原子更新，非法流转抛 `InvalidTransition`。

| 流转 | 条件 |
|------|------|
| `idle → queued` | 设备忙碌入队 |
| `queued → running` | 设备释放 FIFO 出队（原子创建 TestRunRecord） |
| `queued → idle` | 用户取消排队 |
| `running → done` | outcome = `completed` / `stopped` / `interrupted` / `error` |

**状态口径（已收敛小写）**：TaskCard 用小写 `status`（idle/queued/running/done）+ `outcome`（completed/stopped/interrupted/error）；TestRunRecord 用小写 `status`（pending/running/completed/stopped/failed，`models/test_models.py:30-34` `TestRunStatus` 枚举为唯一真相源，迁移 0019 回填存量）。`outcome=interrupted` 时 run 记为 `stopped`。

### 4.2 执行管线口径

- **设备锁**：占用 `device_pool` 锁（`occupied_by = runner-{serial}`，timeout 3600s）；执行结束 / 异常退出兜底释放
- **快照不可变**：启动时 `selected_cases` 完整复制用例步骤 JSON
- **三类型管线**：UI 走 u2 连接 + 设备执行器；API / Web 无设备，走 `ApiAdapter` / `WebAdapter` 统一管线（run_id 前缀 `API-RUN-*` / `WEB-RUN-*`）
- **预检阶段**：锁设备 → 检测在线 → 连接 → 验证能跑用例，预检失败 `_abort_run_before_execute` 善后
- **FIFO 出队**：`_start_next_queued` 先标记占用再出队（原子防竞态）

### 4.3 WS 推送口径

- 路径：`/ws/test-run/{run_id}?token={JWT}`；token 无效 close（code 4001）
- 每条消息带递增 `seq`（run 内单调递增，从 1 起）；前端检测 gap → 触发对账
- 下行 10 种 `type`：`log` / `run_started` / `case_started` / `iteration_result` / `case_finished` / `step_started` / `step_result` / `run_finished` / `device_error` / `heartbeat`
- `heartbeat` 每 5s；`run_finished` 后清理该 run 的 seq 与客户端集合
- 广播 gather + 2s 超时，慢客户端自动剔除不拖垮其他客户端

### 4.4 重启恢复

- **启动恢复**（`recover_orphans`，AppConfig.ready 调用）：孤儿 running 任务 → `done/interrupted`；无活跃进程的 running 记录 → failed；释放 `runner-*` 残留设备锁
- **懒恢复**（`GET /runner/active` / `GET /runner/tasks`）：重建内存队列（从 DB `status=queued` 的任务卡片）、修复 stale running 卡片、修复 `queued` + 终态 outcome 漂移

### 4.5 已知偏差登记

| 偏差 | 说明 |
|------|------|
| 状态大小写 | 已收敛小写：TestRunRecord.status 由迁移 0019（backfill_lowercase_run_status）统一回填为小写，`TestRunStatus` 枚举为小写真相源（pending/running/completed/stopped/failed）；前端 report-generator `constants.ts:53-58` `STATUS_KEYS` 已适配小写 |
| `GET /runner/tasks` 字段 camelCase | tasks[] 内字段为 camelCase（前端直读），信封 `{status, tasks}` 与平台 snake_case 惯例不同（已登记，契约见 §5.3） |
| `run_started` 未消费 | 后端推送 `run_started`，前端未消费（保留为协议扩展点）；前端 `constants.ts` WS 类型表仅 9 种，另处理 `_ws_disconnected` / `_ws_reconnected` 合成事件 |
| mode 取值漂移 | 前端 `EXECUTION_MODES` 存 `now` / `scheduled`，模型默认与注释为 `immediate`（无 choices 约束），按前端口径展示、后端原样落库（已登记） |
| 孤儿组件 | `components/StepScreenshotPanel.vue`（本地）未被引用——详情页使用共享同名组件；`composables/useTaskOperations.ts` 已抽出未接线 |

---

## 5. API 接口功能

鉴权：全部 HTTP 端点需 JWT Bearer；WebSocket 经 query string `token`。JSON 字段 snake_case（`/tasks` 列表内任务对象字段为 camelCase，见 §4.5 偏差）。

### 5.1 端点总览（13 端点）

| # | 方法 | 端点 | 功能 | 前端消费 |
|---|------|------|------|:--:|
| 1 | POST | `/api/runner/run` | 启动执行（F-02-01） | ✅ |
| 2 | GET | `/api/runner/active` | 活跃运行列表 + 懒恢复（F-02-02） | ✅ |
| 3 | POST | `/api/runner/queue/cancel` | 取消排队（F-02-02） | ✅ |
| 4 | POST | `/api/runner/run/{run_id}/stop` | 停止执行（F-02-03） | ✅ |
| 5 | GET | `/api/runner/run/{run_id}/status` | 运行状态查询 | ❌（预留） |
| 6 | GET | `/api/runner/runs` | 运行历史（最近 50 条） | ❌（预留） |
| 7 | POST | `/api/runner/run-step` | 单步调试（F-03-06，用例编辑器消费） | ✅（case-manager） |
| 8 | GET | `/api/runner/tasks` | 任务卡片列表（F-01-01） | ✅ |
| 9 | POST | `/api/runner/tasks/save` | 任务卡片 upsert（F-01-01） | ✅ |
| 10 | DELETE | `/api/runner/tasks/{task_id}` | 删除任务卡片（F-01-01） | ✅ |
| 11 | GET | `/api/runner/monitor/{run_id}` | 运行健康监控（WS 降级轮询） | ❌（预留） |
| 12 | GET | `/api/runner/run/{run_id}/snapshot` | 状态快照（WS 降级兜底） | ❌（预留） |
| 13 | GET | `/api/runner/step-screenshots/{filepath}` | 步骤标注截图服务（F-03-03） | ✅ |

> 另消费 device-pool（契约见 PRD-02）：`acquire_device` / `release_device`；case-manager（契约见 PRD-05）：`get_test_case` 只读用例定义。

### 5.2 端点 1 — 启动执行

**接口地址**：`POST /api/runner/run`

**请求字段**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `case_ids` | array | 是 | 用例 ID 列表 |
| `loop_count` | number | 否 | 循环次数（默认 3） |
| `interval_seconds` | number | 否 | 轮间间隔（最小 5） |
| `task_type` | string | 否 | ui_automation / api_testing / web_automation（默认 ui_automation） |
| `device_serials` / `device_serial` | array / string | UI 必填 | 目标设备（支持多设备并行） |
| `package_name` | string | 否 | 目标包名（缺省取用例 package_name） |
| `client_task_id` | string | 否 | 任务卡片 ID（关联 TaskCard） |
| `start_at` / `end_at` | string | 否 | 定时执行起止（ISO） |

**响应字段**：`status` · `runs[]`（run_id + serial）· `queued[]`（排队设备）· `case_count` · `loop_count` · `parallel`。

**错误**：`case_ids required`（200 status:false）；UI 无设备 → 400「device_serial is required for UI automation tasks」；无可用设备 → 400「没有可用设备…」；无 enabled 用例 →「no enabled test cases found」。

### 5.3 任务卡片（端点 8/9/10）

**接口地址**：`GET /api/runner/tasks` / `POST /api/runner/tasks/save` / `DELETE /api/runner/tasks/{task_id}`

**tasks[] 字段**（camelCase，前端直读）：`id` / `name` / `mode`（前端存 `now`\|`scheduled`，模型默认 `immediate`，见 §4.5 漂移登记）/ `taskType` / `deviceSerial` / `caseIds` / `loopCount` / `intervalSeconds` / `running`（派生自 status）/ `runId` / `caseItems` / `stepStates` / `overallPass` / `overallFail` / `logs` / `createdAt` / `creator` / `currentCaseTitle` / `currentIteration` / `failedSteps` / `status`（idle\|queued\|running\|done）/ `outcome` / `state`（`state_machine.display_state` 权威状态，前端状态判定唯一入口）/ `round` / `conclusion` / `bugTicket` / `startAt` / `endAt` / `perfStats` / `step_details`。

**保存请求**：`id` 必填（400「任务ID不能为空」）+ 表单字段；响应 `{status, id}`。

**删除**：响应 `{status, message:"已删除"}`。

### 5.4 停止 / 取消排队（端点 4/3）

- `POST /api/runner/run/{run_id}/stop`：优雅停止（检查点收尾）；预检阶段返回「stopping (pre-flight)」；不存在返回「run not found or already finished」
- `POST /api/runner/queue/cancel`：请求 `client_task_id` + `device_serial`；缺失 → 400；未找到 → 404「未找到该排队任务，可能已经开始执行」

### 5.5 活跃 / 历史 / 状态（端点 2/6/5）

- `GET /api/runner/active`：`{status, active:[{run_id, status, selected_cases, loop_count, started_at, device_serial, client_task_id}]}`；附带懒恢复副作用
- `GET /api/runner/runs`：`{status, runs:[{run_id, status, device_serial, loop_count, total, passed, failed, started_at, finished_at, selected_cases}]}`（最近 50 条）
- `GET /api/runner/run/{run_id}/status`：活跃时 `{status, run_id, is_running, selected_cases, loop_count, started_at}`；已结束查 DB 附 `total_iterations`/`passed`；404「run not found」

### 5.6 监控 / 快照（端点 11/12）

- `GET /api/runner/monitor/{run_id}`：`{status, run_id, live, is_running, device{serial,status,resolution,sdk,battery}, selected_cases, loop_count, started_at, log_tail(末 50 行)}`；WS 断开时前端可降级轮询
- `GET /api/runner/run/{run_id}/snapshot`：`{status, run_id, live, status, cases:[{case_id,pass,fail,total}], client_task_id}`；WS 降级兜底

### 5.7 单步调试（端点 7）

**接口地址**：`POST /api/runner/run-step`

**请求字段**：`type`（16 种，默认 click）/ `xpath` / `xpath2` / `timeout` / `expected_text` / `index` / `direction` / `distance` / `description` / `device_serial`。

**响应**：pass → `{status:true, result, message, logs[]}`；fail → `{status:false, result, message, logs[]}`；未知类型 →「Unknown step type: {type}」；未选调试设备 →「请先在用例编辑页顶部选择调试设备」。

### 5.8 步骤截图服务（端点 13）

**接口地址**：`GET /api/runner/step-screenshots/{filepath}`

返回 PNG 文件流；路径越界 → 403「invalid path」；不存在 → 404「not found」。

### 5.9 WebSocket — 执行进度

**接口地址**：`WS /ws/test-run/{run_id}?token={JWT}`

**鉴权**：query `token` 校验失败直接 close（code 4001）。

**下行消息**（每条含递增 `seq`）：

| type | 字段 | 说明 |
|------|------|------|
| `log` | `run_id`, `message` | 执行日志 |
| `run_started` | `run_id` | 预检通过正式进入执行 |
| `case_started` | `run_id`, `case_id`, `case_title`, `loop_count` | 用例开始 |
| `iteration_result` | `run_id`, `case_id`, `iteration`, `result`, `duration_ms` | 单轮迭代结果 |
| `case_finished` | `run_id`, `case_id`, `pass`, `fail`, `rate` | 用例完成 |
| `step_started` | `run_id`, `case_id`, `iteration`, `step_index`, `total_steps`, `step_type`, `description` | 步骤开始 |
| `step_result` | 同上 + `result` | 步骤结果 |
| `run_finished` | `run_id`, `summary`, `log_path` | 运行结束（清理 seq 与客户端） |
| `device_error` | `run_id`, `message` | 设备异常 |
| `heartbeat` | `run_id` | 每 5s 心跳 |

### 5.10 契约变更

| 版本 | 变更 |
|------|------|
| v7.x | WS 路径由 `/ws/test-run/{taskId}` 更正为 `/ws/test-run/{run_id}`（run 粒度，非任务卡片粒度） |
| v7.x | 新增 TREP v1.0：WS 消息统一 `seq` 递增序号 + 5s 心跳；新增 `/monitor/{run_id}`、`/run/{run_id}/snapshot` 降级端点 |
| v8.0 | 端点总览校正为 13 端点（含 `/step-screenshots/{filepath}` 与 `/tasks/{task_id}`）；无字段契约破坏 |

---

## 6. 数据来源表

| 表 | 表前缀 | 说明 |
|------|:--:|------|
| `tr_task_cards` | tr_ | 任务卡片（跨设备同步；状态/outcome/快照聚合字段） |
| `tr_test_runs` | tr_ | 测试运行记录（run_id 唯一；selected_cases 执行快照；status 小写） |
| `tr_test_results` | tr_ | 单轮迭代结果（case_id 非 FK 支持多态用例；step_details 含截图路径） |
| `tr_test_sop` | tr_ | AI SOP 四阶段上下文（AI 助手 Tool 消费） |
| `dp_devices` | dp_ | 只读：设备锁/占用（经 device_pool api，主权 PRD-02） |
| `cm_test_definitions` 等 | cm_ | 只读：用例定义（经 case-manager，主权 PRD-05） |

---

## 7. 非功能需求

| 类别 | 指标 | 目标值 |
|------|------|------|
| 性能 | 任务列表 | GET /tasks 上限 200 条，单查询无 N+1 |
| 性能 | 运行历史 | GET /runs 上限 50 条 |
| 可靠性 | WS 心跳 | 每 5s；前端 15s 无心跳判连接丢失 |
| 可靠性 | WS 重连 | 指数退避 1s→2s→4s→8s→16s（最多 5 次） |
| 可靠性 | 重启恢复 | 孤儿 running → interrupted；stale running → failed；释放 runner-* 设备锁 |
| 可靠性 | 日志容量 | 前端上限 1000 条，超出裁剪到 500 条 |
| 一致性 | 状态流转 | 全部经 state_machine 事务原子更新，非法流转拒绝 |
| 安全 | WS 鉴权 | token 无效直接断开（code 4001） |
| 安全 | 截图路径 | 越界 403 拦截（限定 SCREENSHOT_DIR 内） |

---

## 8. 非目标（Non-goals）

| 不做的功能 | 原因 |
|------|------|
| 用例定义管理 | 由 case-manager（PRD-05）承担，本模块只读消费 steps_json |
| 设备注册/连接初始化 | 由 device-pool（PRD-02）承担 |
| 报告内容生成 | 由 report-generator（PRD-07）承担，本模块只落执行记录 |
| 队列持久化到独立存储 | 采用 DB 任务卡片（queued）+ 启动/懒恢复方案，不引入消息队列中间件 |
| AI 自然语言编排 | 由 ai-assistant（PRD-08）经 Tool 调用本模块 |

---

## 9. 关键约束速查

| 编号 | 约束 | 实施位置 |
|------|------|------|
| C-01 | 状态流转唯一入口：禁止绕过 state_machine 直接改状态 | `state_machine.py` |
| C-02 | 执行前快照用例（selected_cases 不可变） | `state_machine.dequeue` / `runner.py` |
| C-03 | 设备锁走 device_pool api（`runner-{serial}` 前缀占用，3600s） | `views/execution.py` |
| C-04 | 写库收敛：View → api.py / state_machine → ORM | `api.py` / `state_machine.py` |
| C-05 | 响应统一 `{status, data|message}`；`/tasks` 列表内 camelCase（登记偏差） | 全部端点 |
| C-06 | WS 消息带 seq + 5s 心跳；路由注册在 gateway | `callbacks.py` / `gateway/routing.py` |
| C-07 | 重启恢复：recover_orphans（启动）+ 懒恢复（active/tasks） | `state_machine.py` / `views/run_views.py` |
| C-08 | 截图文件服务限定 SCREENSHOT_DIR 内（403 越界） | `views/task_views.py` |
| C-09 | 跨模块 import 收敛：前端组件禁止直连 case-manager/device-pool api | `frontend/src/modules/test-runner/api.ts` |

---

## 10. 相关文件索引

| 层 | 文件 | 说明 |
|------|------|------|
| 前端 | `frontend/src/modules/test-runner/index.vue` | 主页面编排（KPI + 筛选 + 双视图） |
| 前端 | `frontend/src/modules/test-runner/components/NewTaskDialog.vue` | 新建任务弹窗 |
| 前端 | `frontend/src/modules/test-runner/components/TaskDetail.vue` | 任务详情页（5 功能区） |
| 前端 | `frontend/src/modules/test-runner/api.ts` | 本模块 7 端点函数 + 4 跨模块封装（用例/设备） |
| 前端 | `frontend/src/modules/test-runner/composables/useTaskWebSocket.ts` | WS 连接/消息分发/重连/seq 检测 |
| 前端 | `frontend/src/modules/test-runner/composables/taskUtils.ts` | 状态判定 / 进度计算 / ID 生成 |
| 前端 | `frontend/src/modules/test-runner/composables/useDebouncedSave.ts` | 任务保存防抖 |
| 前端 | `frontend/src/modules/test-runner/composables/useQueuePoller.ts` | 排队轮询（active 驱动出队） |
| 前端 | `frontend/src/modules/test-runner/constants.ts` / `routes.ts` | 常量 / 路由 `/runner`、`/runner/task/:taskId` |
| 后端 | `apps/test_runner/urls.py` | 13 端点路由 |
| 后端 | `apps/test_runner/views/`（execution/run_views/task_views/executor/helpers） | HTTP 入口 |
| 后端 | `apps/test_runner/views/execution_steps.py` | 执行生命周期步骤（DB 持久化 + 状态机流转桥接） |
| 后端 | `apps/test_runner/views/ai_execution.py` | AI 工具触发的单设备 UI 执行编排 |
| 后端 | `apps/test_runner/recovery_helpers.py` | 任务卡片孤儿检测（保护已分配 run_id 的任务免误判中断） |
| 后端 | `apps/test_runner/state_machine.py` | 状态机（唯一流转入口 + 重启恢复） |
| 后端 | `apps/test_runner/runner.py` / `remote_runner.py` | UI / API / Web 执行器 |
| 后端 | `apps/test_runner/callbacks.py` / `consumers.py` | WS 回调广播 / Consumer |
| 后端 | `apps/test_runner/api.py` | 跨模块写白名单（save/delete_task_card、resolve_creator） |
| 后端 | `apps/test_runner/models.py` | 4 表定义 |
| 路由 | `config/urls.py` | `api/runner/` |
| 路由 | `gateway/routing.py` | `ws/test-run/{run_id}` |

---

## 附录A：功能边界规则

| 边界 | 规则 |
|------|------|
| 我能做什么 | 任务卡片 CRUD、UI/API/Web 三类执行、FIFO 排队、定时执行、停止/重跑/取消、单步调试、实时进度推送、缺陷聚合 |
| 我不能做什么 | 管理用例定义（PRD-05）、元素资产 CRUD（PRD-04）、设备检查/实时截图（PRD-03）、注册/连接设备（PRD-02）、生成报告内容（PRD-07）、AI 编排（PRD-08） |
| 如需越界 | 设备经 device_pool api 锁/释放；用例经 case-manager 只读；报告数据由 report-generator 实时读取本模块 tr_ 表 |
| 数据可见性 | 任务卡片/执行记录为平台共享（历史审计可追溯）；执行快照不随用例修改而变 |
