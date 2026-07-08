# 子PRD — 执行引擎 (Test Runner)

> 关联模块：`apps/test_runner/` · 前端：`frontend/src/modules/test-runner/`
> 关联全局：`../全局PRD.md` · 关联用例：`../子PRD/03-case-manager.md` · 关联设备：`../子PRD/02-device-pool.md` · 关联报告：`../子PRD/05-report-generator.md`
> 版本：v4.2 · 状态：已实现 · 日期：2026-07-07

---

## 1. 模块功能目标

执行引擎是测试平台的**任务调度与用例执行中枢**，核心职责：

1. **任务卡片管理**：创建、编辑、删除测试执行任务卡片，指定目标设备、选择用例、设置循环次数。任务卡片跨设备同步（数据库持久化）
2. **设备调度**：提交任务时检查设备忙碌状态——空闲设备立即执行，忙碌设备自动排队等待。设备释放后按 FIFO 顺序调度下一个排队任务
3. **测试用例执行**：从用例工程加载 TestDefinition → 解析 steps_json → 驱动设备按 14 种步骤类型执行，含完整的错误处理、超时控制、日志记录
4. **实时进度推送**：WebSocket 实时推送每个步骤的执行结果、日志、迭代进度。多设备并行执行
5. **执行控制**：中途停止执行、取消排队任务、循环执行（loop count）
6. **执行快照与审计**：执行前快照用例步骤到 TestRunRecord.selected_cases，确保历史可审计

### 用户故事

| # | 角色 | 故事 | 验收标准 |
|---|------|------|----------|
| US-01 | 测试工程师 | 作为**测试工程师**，我希望**选择设备和用例后一键创建并执行任务**——系统自动判断设备是否忙碌，空闲则立即执行，繁忙则加入排队，我不需要手动检查设备状态 | 点击「创建并执行」后设备空闲则立即开始执行；设备忙则自动排队并提示「设备正忙，任务已加入队列」；排队任务设备空闲后自动开始执行 |
| US-02 | 测试工程师 | 作为**测试工程师**，我希望**查看所有任务的实时状态**——执行中、等待中、已完成、未完成、未执行六个标签页一目了然，执行中的任务可以看到实时日志和进度 | 6 个 Tab 分别展示对应状态的任务卡片；执行中卡片显示当前用例名和迭代进度；完成卡片显示通过/失败数 |
| US-03 | 测试工程师 | 作为**测试工程师**，我希望**随时停止正在执行的任务**——点击停止后设备释放并自动启动下一个排队任务 | 点击停止 → 确认弹窗 → 任务状态变为已完成并记录 stopped 状态；底层的 asyncio 任务被终止；设备释放后下一个排队任务自动开始 |
| US-04 | 测试工程师 | 作为**测试工程师**，我希望**取消排队中的任务**——点击取消后任务回到未执行列表，保留任务配置（设备、用例、循环次数），我可以稍后重新执行 | 取消排队后任务从等待列表移除回到未执行列表；设备队列中对应条目被移除；任务卡片保留不丢失 |
| US-05 | 测试负责人 | 作为**测试负责人**，我希望**在 A 电脑创建的任务能够在 B 电脑上看到**——任务卡片数据存储在服务器数据库而非浏览器本地 | A 电脑创建任务后 B 电脑刷新页面任务出现；任务状态变更跨设备同步 |
| US-06 | 测试工程师 | 作为**测试工程师**，我希望**点击任务卡片查看执行详情**——包括每个用例的通过/失败状态、执行日志、失败步骤信息 | 详情页展示所有用例的执行结果表格；每个用例有通过/失败统计；日志可展开查看 |
| US-07 | 测试负责人 | 作为**测试负责人**，我希望**执行完成后能查看历史记录**——知道什么时候、在哪个设备上、用哪些用例执行了什么测试，即使用例后来被修改了，历史记录仍然能还原当时的步骤 | TestRunRecord 持久化执行快照；selected_cases 包含执行时用例的完整步骤数据 |
| US-08 | 测试工程师 | 作为**测试工程师**，我希望**删除不需要的任务卡片**——执行中任务先停止再删除，已完成的直接删除 | 执行中任务删除时自动发送停止指令；删除时二次确认；删除后从列表和数据库同时移除 |
| US-09 | 测试工程师 | 作为**测试工程师**，我希望**每个任务卡片都有进度条**——一眼就能看出已执行了多少次、总共需要执行多少次，不管任务处于未执行、执行中还是已完成状态 | 全部任务卡片显示进度条和"已执行 X/Y 次"文字；完全通过显示"✅ 全部通过"；中途停止显示"⏹ 已中止"；未执行的进度为 0% |
| US-10 | 测试工程师 | 作为**测试工程师**，我希望**重新执行任务时创建一个全新的任务卡片**——新 ID、名称标注"第N轮"，旧卡片保留历史结果不变，这样我可以对比多轮执行的结果 | 点击重新执行 → 创建新任务卡片（新 ID）；名称自动加"第2轮"/"第3轮"后缀；配置从原任务复制；原任务卡片不变 |

### 1.1 任务生命周期状态机

```
                     ┌──────────────────────────┐
                     │       未执行 (idle)        │
                     │  caseItems=[]  running=F  │
                     └──────────┬───────────────┘
                                │ 点「执行」
                                ▼
                     ┌──────────────────────┐
                     │   检查设备是否忙碌？    │
                     └──────┬───────┬───────┘
                            │ 空闲   │ 忙碌
                            ▼        ▼
              ┌──────────────┐  ┌──────────────┐
              │ 执行中(running)│  │ 等待中(queued) │
              │ running=T    │  │ running=F     │
              │ runId 已分配  │  │ runId 为空     │
              └──────┬───────┘  └──────┬───────┘
                     │                  │
              点「停止」          点「取消排队」
                     │                  │
                     ▼                  ▼
              ┌──────────────┐  ┌──────────────┐
              │ 未完成(incomplete)│ 未执行(idle)   │
              │ running=F    │  │ 保留配置       │
              │ outcome=     │  │ 可重新执行     │
              │ stopped/     │  └──────────────┘
              │ interrupted/ │
              │ error        │
              └──────────────┘
                     │
              正常执行完成
                     │
                     ▼
              ┌──────────────┐
              │ 已完成(completed)│
              │ running=F    │
              │ outcome=     │
              │ completed    │
              └──────────────┘
                     │
              设备空闲 ──→ 下一个排队任务自动转为执行中
```

**5 种任务状态**：

| 状态 | status 字段 | 前端 Tab | 判断条件 |
|------|------------|---------|---------|
| 未执行 | `idle` | 📝 未执行 | caseItems 为空，从未启动 |
| 等待中 | `queued` | ⏳ 等待中 | 已入队，caseItems[0].status='pending' |
| 执行中 | `running` | ⚡ 执行中 | running=true，WebSocket 已连接 |
| 未完成 | `done` | ⏹ 未完成 | running=false, caseItems 非空, outcome 为 stopped/interrupted/error |
| 已完成 | `done` | ✅ 已完成 | running=false, outcome='completed' |

> **注意**：`status` 字段只有 4 个值（idle/queued/running/done），"已完成"和"未完成"通过 `outcome` 字段在 `done` 状态下做二级区分。

### 1.2 模块边界

```
case-manager (TestDefinition + steps_json)
      │
      ▼ 加载用例定义
device-pool (设备实例 + u2 连接)
      │
      ▼ 获取设备
test-runner (执行引擎)
      │
      ├─ StepExecutor (14 种步骤) ← DeviceAdapter (uiautomator2)
      ├─ WebSocket Consumer (实时推送)
      ├─ TestRunRecord (执行快照)
      ├─ TestResult (单次迭代结果)
      ├─ TaskCard (任务卡片, 跨设备同步)
      │
      ▼ 输出执行结果
report-generator (CSV/JSON 测试报告)
```

---

## 2. 功能详细说明

### 2.1 F-01：任务卡片管理

**概述**：用户创建测试执行任务卡片，选择设备和用例，设置循环次数。任务卡片持久化到数据库，支持跨设备同步。

**数据模型**：`tr_task_cards` 表（TaskCard 模型）

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | VARCHAR(50) PK | 任务 ID（格式 ID-001） |
| name | VARCHAR(200) | 任务名称 |
| creator | VARCHAR(200) | 创建者用户名 |
| mode | VARCHAR(20) | immediate / scheduled |
| device_serial | VARCHAR(200) | 目标设备序列号 |
| case_ids | JSON | 选中的用例 ID 列表 |
| loop_count | INT | 循环次数 |
| running | BOOL | 是否正在执行 |
| run | FK→TestRunRecord | 关联的执行记录（运行时填充） |
| case_items | JSON | 用例执行状态数组 |
| step_states | JSON | 步骤执行状态 |
| overall_pass / overall_fail | INT | 通过/失败计数 |
| logs | JSON | 执行日志（保留最近 100 条） |
| conclusion | TEXT | 执行结论 |
| bug_ticket | TEXT | Bug 票据 |
| failed_steps | JSON | 失败步骤详情 |
| created_at / updated_at | DateTime | 时间戳 |

**API 端点**：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/runner/tasks` | 列出全部任务卡片 |
| POST | `/api/runner/tasks/save` | 创建/更新任务卡片（upsert） |
| DELETE | `/api/runner/tasks/{task_id}` | 删除任务卡片 |

**持久化策略**：
- 任务创建时立即调 `saveTaskToServer(task)` 写入数据库
- 状态变更时通过 `scheduleSave()` 防抖保存（1 秒延迟）
- 任务删除时调 API 删除数据库记录
- 前端 localStorage 已移除（v4.0），全部走数据库

### 2.2 F-02：设备调度与排队

**概述**：后端检查设备忙碌状态，空闲设备立即执行，忙碌设备自动排队。

**后端逻辑**（`start_test_run`）：
1. 遍历选中的设备序列号
2. 验证设备存在且状态为 ONLINE
3. 检查 `is_device_busy(serial)` → 内存 `_device_busy` 集合
4. 空闲：创建 u2 连接 → 生成 `run_id` → `asyncio.create_task` 异步执行
5. 忙碌：`_enqueue(serial, payload)` → 加入该设备的 FIFO 队列

**出队逻辑**（`_start_next_queued`）：
- `_execute_tests` 的 `finally` 块中触发
- 从队列取出下一个任务 → 标记设备忙碌 → 创建新 run_id → 执行
- `_run_client_task[run_id] = client_task_id` 使前端轮询可检测到

**前端感知**：
- 3 秒轮询 `GET /api/runner/active`，匹配 `active.client_task_id`
- 检测到匹配 → 设 `task.running = true` + `task.runId = active.run_id` → 连接 WebSocket
- 所有排队任务消失时停止轮询

**取消排队**（`cancel_queued_task`）：
- `POST /api/runner/queue/cancel` + `{client_task_id, device_serial}`
- 从 `_device_queue[serial]` 中移除匹配项
- 前端将任务状态重置为「未执行」

### 2.3 F-03：任务执行

**执行流程**：
```
POST /api/runner/run {case_ids, loop_count, device_serial, client_task_id}
  → 加载 TestDefinition → 构建 TestCaseDef
  → 创建 TestRunRecord（含 selected_cases 快照）
  → TestRunner.run(run_id, test_cases, loop_count)
       → 逐用例、逐迭代、逐步执行
       → WebSocket 实时推送进度
  → persist() 写 TestResult（run FK + case FK）
  → 更新 TestRunRecord status + summary
  → finally: _start_next_queued(serial) 出队
```

**14 种步骤执行**：设备适配器 `DeviceAdapter` 封装 uiautomator2 操作，`StepExecutor` 按步骤类型分发。

**执行快照**：`TestRunRecord.selected_cases` 存储执行时用例的 `{case_id, title, steps_data}` 完整快照。

### 2.4 F-04：实时进度推送

**WebSocket**：`ws://host/ws/test-run/{runId}?token=JWT`

**消息类型**：

| 类型 | 触发时机 | 载荷 |
|------|---------|------|
| `log` | 每步执行后 | `{message, level}` |
| `case_started` | 用例开始 | `{case_id, title, total_iterations}` |
| `step_result` | 步骤执行完成 | `{case_id, iteration, step_index, result, detail}` |
| `iteration_result` | 迭代完成 | `{case_id, iteration, result, duration_ms}` |
| `case_finished` | 用例完成 | `{case_id, passed, failed}` |
| `run_finished` | 全部执行完成 | `{summary, csv_path}` |
| `device_error` | 设备异常 | `{message}` |

### 2.5 F-05：执行控制

**停止运行中任务**：
- `POST /api/runner/run/{run_id}/stop`
- 设置 `_RunState.is_running = False` → 执行循环检测到后停止
- 前端关闭 WebSocket，设 `task.running = false`

**取消排队任务**：
- `POST /api/runner/queue/cancel`
- 从设备队列移除 → 前端重置 `caseItems = []`，任务回到「未执行」

**循环执行**：通过 `loop_count` 参数控制每用例执行 N 次。

### 2.6 F-06：进度展示与结果状态

**概述**：每张任务卡片都显示执行进度条和状态标签，区分四种终态。

**进度条**：
- 始终渲染（包括未执行任务，进度 0%）
- 进度 = `已执行次数 / 总次数 × 100`
- 总次数 = caseItems 非空时用迭代累计，为空时用 `caseIds.length × loopCount` 预估
- 颜色随状态变化（执行中蓝色 / 已完成绿色 / 未完成红色）
- 进度 > 0 时显示百分比数字，0% 时不显示

**四种结果状态**：

| 状态 | outcome 值 | 触发条件 | 标签 | Tab |
|------|-----------|---------|------|-----|
| 已完成 | `'completed'` | 正常执行完成（WebSocket `run_finished`） | ✅ 已完成 | ✅ 已完成 |
| 未完成 | `'stopped'` | 用户点击停止 | ⏹ 未完成 | ⏹ 未完成 |
| 运行中断 | `'interrupted'` | 服务器重启恢复孤儿任务 | ⚠️ 运行中断 | ⏹ 未完成 |
| 异常终止 | `'error'` | 设备异常/执行崩溃 | 💥 异常终止 | ⏹ 未完成 |
| 未执行 | `''` | 排队取消 / 从未执行 | 📝 未执行 | 📝 未执行 |

**进度文字**：
- 全部任务：「已执行 X/Y 次」
- 已完成：「已执行 X/Y 次 · ✅ 全部通过」
- 未完成：「已执行 X/Y 次 · ⏹ 已中止」
- 执行中：「已执行 X/Y 次（第 N 轮循环）」

### 2.7 F-07：重新执行创建新卡片

**概述**：点击「重新执行」不修改原任务，而是创建一个全新的任务卡片。

**行为**：
1. 生成新任务 ID（`ID-{seq}`）
2. 名称 = `{原名去掉旧轮次} 第{轮次+1}轮`（如「登录测试」→「登录测试 第2轮」）
3. 复制原任务的 `deviceSerial`、`caseIds`、`loopCount`、`mode`
4. 新卡片 `caseItems`、`logs`、`outcome` 等执行状态为空
5. 立即保存到数据库 → 自动执行

**用途**：多轮测试结果对比，每轮独立卡片可追溯。

---

## 3. 数据模型

### 3.1 任务卡片（tr_task_cards）

见 §2.1

### 3.2 测试运行记录（tr_test_runs）

| 字段 | 类型 | 说明 |
|------|------|------|
| run_id | VARCHAR(200) PK | 运行 ID |
| status | VARCHAR(50) | PENDING/RUNNING/PASSED/FAILED/STOPPED |
| device_serial | VARCHAR(200) | 执行设备 |
| selected_cases | JSON | 执行时用例快照 `[{case_id, title, steps_data}]` |
| loop_count | INT | 循环次数 |
| summary | JSON | 结果摘要 |
| started_at / finished_at | VARCHAR(100) | 起止时间 |

### 3.3 测试结果（tr_test_results）

| 字段 | 类型 | 说明 |
|------|------|------|
| run | FK→TestRunRecord | 关联运行记录 |
| case | FK→TestDefinition (SET_NULL, db_column='case_id') | 关联用例 |
| iteration | INT | 迭代序号 |
| result | VARCHAR(50) | pass/fail/error |
| duration_ms | FLOAT | 耗时 |
| detail | TEXT | 详情 |

### 3.4 测试 SOP 上下文（tr_test_sop）

AI 助手四阶段工作流的持久化状态存储。

---

## 4. API 端点总览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/runner/run` | 启动测试执行 |
| POST | `/api/runner/run/{run_id}/stop` | 停止执行 |
| GET | `/api/runner/run/{run_id}/status` | 查询运行状态 |
| GET | `/api/runner/runs` | 历史运行列表 |
| GET | `/api/runner/active` | 当前活跃运行 |
| POST | `/api/runner/queue/cancel` | 取消排队任务 |
| GET | `/api/runner/tasks` | 列出任务卡片 |
| POST | `/api/runner/tasks/save` | 保存任务卡片 |
| DELETE | `/api/runner/tasks/{task_id}` | 删除任务卡片 |
| POST | `/api/runner/run-step` | 单步调试执行 |

---

## 5. 关键约束与规则

| 规则 | 说明 |
|------|------|
| FIFO 排队 | 同设备多任务按到达时间顺序执行 |
| 设备独享 | 一台设备同一时刻只执行一个任务 |
| 执行快照 | 执行前保存用例步骤快照，确保历史可审计 |
| case_id FK | SET_NULL 保护历史结果，删用例不删结果 |
| 排队任务可取消 | 取消后任务保留配置回到未执行状态 |
| 跨设备同步 | 任务卡片存数据库，不依赖浏览器 localStorage |

---

## 6. 前端组件树

```
index.vue（主页面 /runner）
├── PageHeader
├── 新建任务按钮 + Modal 表单
├── Tabs（全部/执行中/等待中/已完成/未完成/未执行）
├── 任务卡片列表
│   ├── 状态标签（⚡执行中/⏳等待中/✅已完成/⏹未完成/⚠️运行中断/💥异常终止/📝未执行）
│   ├── 设备名 + 用例数 + 循环次数
│   ├── 进度条 + 进度文字
│   └── 操作按钮（执行/停止/取消排队/删除/重新执行）
├── WebSocket 实时更新
└── 排队轮询（1.5秒间隔）

TaskDetail.vue（详情页 /runner/task/:id）
├── 任务信息头
├── 用例执行结果表格
├── 实时日志面板
├── 结论与 Bug 票据
└── WebSocket 实时更新
```

---

## 7. 后端文件结构

```
apps/test_runner/
├── models.py          TaskCard / TestRunRecord / TestResult / TestSOP
├── views.py           10 个 HTTP 端点 + 排队管理
├── runner.py          TestRunner 执行引擎 + _active_runs 管理
├── executor.py        StepExecutor（14 种步骤分发）
├── adapter.py         DeviceAdapter（uiautomator2 封装）
├── callbacks.py       TestRunnerCallback → WebSocket 推送
├── consumers.py       TestRunConsumer（WebSocket）
├── urls.py            10 条路由
├── admin.py           4 个 Admin 注册
└── api.py             持久化帮助函数
```

---

## 8. 当前限制与未来规划

### 已实现 ✅
- 任务卡片 CRUD + 数据库持久化
- 设备繁忙检测 + FIFO 排队
- 排队任务取消 API
- 执行快照（selected_cases）
- case_id FK 约束（SET_NULL）
- WebSocket 实时进度推送
- 多设备并行执行
- 循环执行 + 中途停止

### 规划中 📋
- 队列状态持久化到 TaskCard.status（目前 `_device_queue` 仍是内存结构）
- 服务器重启后排队任务恢复
- WebSocket 断线自动重连
- TaskDetail.vue 统一使用 API（目前仍用 localStorage）
- 后端主动更新 TaskCard 状态
- 定时执行（schedule）

---

## 变更记录

| 版本 | 日期 | 类型 | 说明 |
|------|------|------|------|
| v4.0 | 2026-07-07 | 重写 | 基于代码实现完整逆向：TaskCard 模型与跨设备同步、排队取消 API、case_id FK 约束、selected_cases 执行快照、4 状态任务生命周期、10 API 端点、4 数据表 |
| v4.1 | 2026-07-07 | 新增 | **进度条与结果状态** — (F-06 新增) 全体任务卡片显示进度条，三种终态区分（已完成/未完成/未执行），进度文字标注执行统计；(F-07 新增) 重新执行创建新卡片（新 ID + 第N轮后缀），原卡片保留历史不覆盖；(US-09/US-10 新增) |
| v4.2 | 2026-07-07 | 重构 | **状态机升级** — 5 状态模型：idle→queued→running→done(completed/incomplete)；前端 Tab 从 4 个扩展为 6 个（全部/执行中/等待中/已完成/未完成/未执行）；新增 `error` outcome（异常终止）；排队轮询间隔优化为 1.5s；TaskCard.status 与 outcome 协同工作：status 管生命周期（idle/queued/running/done），outcome 管终态细分（completed/stopped/interrupted/error） |
