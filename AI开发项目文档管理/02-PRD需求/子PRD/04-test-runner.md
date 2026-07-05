# 子PRD — 执行引擎 (Test Runner)

> 关联模块：`apps/test_runner/` · 前端：`frontend/src/modules/test-runner/`
> 关联全局：`../全局PRD.md` · 关联用例：`../子PRD/03-case-manager.md` · 关联设备：`../子PRD/02-device-pool.md` · 关联报告：`../子PRD/05-report-generator.md`
> 版本：v2.0 · 状态：草稿 · 日期：2026-06-30

---

## 1. 模块功能目标

执行引擎是测试平台的核心执行中枢，承担以下核心职责：

1. **测试用例加载与执行**：从用例工程（case-manager）获取 TestDefinition，解析 steps_json 构建 TestCaseDef，驱动设备按步骤序列执行
2. **14 种步骤的原生执行**：将抽象的步骤描述（click / wait / verify_text 等）转换为 uiautomator2 的底层设备操作，包含完整的错误处理、超时控制、日志记录
3. **实时进度推送**：通过 WebSocket 向客户端实时推送每个步骤的执行结果、日志、迭代进度，完成时自动生成测试报告
4. **执行控制**：支持循环执行（loop count）、中途停止、多设备并行执行

### 1.1 模块边界

```
case-manager (TestDefinition + steps_json)
      │
      ▼ 加载用例定义
device-pool (设备实例 + 锁)
      │
      ▼ 获取设备 + u2 连接
test-runner (执行引擎)
      │
      ├─ StepExecutor (14 种步骤) ← adapter.py (DeviceAdapter)
      │
      ▼ 结果 → report-generator (CSV/MD/LOG)
```

---

## 2. 功能清单与概述

| 编号 | 功能名称 | 优先级 | 一句话描述 |
|:--:|------|:--:|------|
| F-01 | 异步测试执行 | P0 | 加载用例 → 创建 TestRunner → async 后台异步执行 → 返回 run_id + WS 地址 |
| F-02 | 14 种步骤执行引擎 | P0 | StepExecutor 将每种步骤类型映射到 uiautomator2 操作，含完整的超时控制和错误处理 |
| F-03 | WebSocket 实时推送 | P0 | 每步骤执行结果实时推送前端（日志/迭代结果/用例完成/运行完成/设备错误） |
| F-04 | 执行控制 | P1 | 支持循环执行、中途停止、多设备并行、执行历史查询 |

---

## 3. 功能详细规格

---

### 3.1 F-01：异步测试执行

#### 3.1.1 需求定义

用户选择设备和用例后，点击「执行」按钮触发异步测试执行。后端加载用例定义，构建 TestRunner，通过 asyncio.create_task 在后台异步运行，立即返回 run_id 和 WebSocket 地址。

#### 3.1.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 执行启动响应 | POST /api/runner/run → 返回 run_id | ≤300ms |
| 执行成功率 | 所有步骤 pass / 总步骤数 | ≥95% |
| 步骤超时不阻塞 | 单步骤超时后继续下一迭代 | 100% |

#### 3.1.3 触发条件

- 用户在 test-runner 页面选择用例 + 设置循环次数
- 点击「开始执行」按钮

#### 3.1.4 业务规则

```
用户点击「开始执行」
    ├─ 无设备连接 → ❌ 提示「请先在设备管理中连接设备」
    ├─ 未选用例 → ❌ 提示「请至少选择一个用例」
    ├─ 设备被他人锁定 → ❌ 提示「设备已被 {locked_by} 占用」
    └─ 可用 →
        1. POST /api/runner/run { case_ids, loop_count, device_serial }
        2. 后端 (async)：
           a. 查询 TestDefinition WHERE id IN case_ids AND enabled=true
           b. 解析 steps_json → TestCaseDef 列表
           c. 构建 TestRunRecord (PENDING)
           d. asyncio.create_task → TestRunner.run(run_id, cases, loop_count)
           e. 立即返回 { run_id, ws_url: "/ws/test-run/{run_id}" }
        3. 前端连接 WS 接收实时进度
        4. 执行完成 → runner 调用 ReportGenerator 生成报告文件
```

**执行架构**：
```
TestRunner.run()
  ├─ 创建 DeviceAdapter (u2 设备实例, 线程池中)
  ├─ 创建 StepExecutor (adapter)
  ├─ FOR EACH case:
  │   ├─ callback.on_case_started(case)
  │   ├─ FOR i IN range(loop_count):
  │   │   ├─ executor.execute_all(case.steps_data)
  │   │   │   → 顺序执行每个 step，遇 fail/stopped 则停止
  │   │   ├─ callback.on_iteration_result(result)
  │   │   └─ 如果 is_running=false → 停止
  │   └─ callback.on_case_finished(summary)
  ├─ 更新 run_model: status=COMPLETED
  ├─ 调用 ReportGenerator.save_csv + save_log
  └─ callback.on_run_finished(summary)
```

#### 3.1.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| 用例选择 | el-select 多选，列表从 `GET /api/cases/definitions` 加载 |
| 循环次数 | el-input-number，默认 1，最大 1000 |
| 执行按钮 | 点击后 disabled + loading，显示"执行中..." |
| 日志面板 | 暗色终端风格，Consolas 字体，黑底灰字，日志行自动滚动到底部 |
| 执行进度 | 顶部进度条：已完成迭代 / 总迭代数 |
| 执行动画 | 按钮脉冲动画（anime.js），日志行逐行滑入 |

#### 3.1.6 后端接口要求

| 接口 | 核心行为 |
|------|---------|
| `POST /api/runner/run` (async) | 加载用例 → 创建 TestRunRecord → asyncio.create_task 启动 TestRunner。详见附录 §4.3.1 |

---

### 3.2 F-02：14 种步骤执行引擎

#### 3.2.1 需求定义

StepExecutor 接收 TestStep 序列，按类型分发到对应的方法。每个方法通过 DeviceAdapter 操作设备，返回 'pass' / 'fail' / 'stopped'。遇到第一个非 pass 即终止执行。

#### 3.2.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 步骤执行正确率 | 每种类型自动化测试覆盖 | 100% |
| 超时控制准确性 | 步骤超时后不超过 ±2s 返回 | 100% |
| 日志完整性 | 每步骤记录开始/结束/耗时/结果 | 100% |

#### 3.2.3 触发条件

- StepExecutor.execute_all(steps) 被 TestRunner 调用

#### 3.2.4 业务规则

**14 种步骤执行逻辑**：

| # | 步骤类型 | 执行逻辑 | 成功条件 | 失败条件 |
|---|----------|----------|----------|----------|
| 1 | `click` | 通过 XPath 查找元素 → 点击 | 元素存在且点击成功 | 超时未找到元素 |
| 2 | `click_indexed` | 通过 XPath 查找元素列表 → 取第 index 个 → 点击 | 元素存在且点击成功 | index 超出范围或超时 |
| 3 | `wait` | 轮询检查元素出现（interval=index, max=timeout） | 元素在超时前出现 | 超时未出现或 stopped |
| 4 | `wait_disappear` | 等待元素出现 → 等待元素消失 | 元素出现后消失 | 元素未出现或未消失 |
| 5 | `wait_either` | 同时轮询两个元素（xpath + xpath2），返回先出现的 | 任一元素出现 | 均未出现或 stopped |
| 6 | `wait_toast` | XPath 查找 + u2 toast API 双通道 | Toast 文本匹配 expected_text | 超时未匹配 |
| 7 | `verify_text` | 获取元素 text 属性 → 比对 expected_text | 文本匹配 | 不匹配或元素不存在 |
| 8 | `poll_text` | 轮询获取元素 text → 比对 expected_text | 文本变为期望值 | 超时未变 |
| 9 | `sleep` | sleep(timeout)，每 100ms 检查 is_running | 完成等待 | 被 stopped 中断 |
| 10 | `kill_app` | adb shell am force-stop {package} | 执行成功 | — |
| 11 | `start_app` | adb shell am start {package} | 执行成功 | — |
| 12 | `restart_app` | kill + sleep(index) + start + sleep（默认 5s 等待） | 重启后 App 响应 | — |
| 13 | `retry_click` | 点击 + 等待目标出现，最多重试 index 次 | 目标出现 | 全部重试失败 |
| 14 | `log` | 仅输出 description 到日志 | 总是成功 | — |

**执行约束**：
- 每步骤记录执行耗时（duration_ms）
- 验证步骤（verify_text / poll_text / wait_toast）失败时记录实际文本
- stopped 状态（用户中途停止）不视为 fail

#### 3.2.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| 日志显示 | 通过 WebSocket 的 log 事件实时追加到日志面板 |
| 步骤标注 | 日志行前缀：`[PASS]` 绿色 / `[FAIL]` 红色 / `[STOPPED]` 灰色 |
| 执行进度 | iteration_result 事件更新进度条 + 结果计数 |

#### 3.2.6 后端接口要求

无独立 API 接口，StepExecutor 作为 TestRunner 内部组件运行。关键类：
- `DeviceAdapter`：封装 u2 设备操作（adapter.py）
- `StepExecutor`：步骤分发执行（executor.py）
- `TestRunner`：编排调度（runner.py）

---

### 3.3 F-03：WebSocket 实时进度推送

#### 3.3.1 需求定义

执行过程中，所有关键事件（日志输出、每次迭代结果、用例完成、运行完成、设备错误）通过 WebSocket 实时推送到前端，前端据此更新进度条、日志、结果统计。

#### 3.3.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 推送延迟 | 事件发生 → 前端收到 | ≤200ms |
| 事件完整性 | 所有迭代结果均推送 | 100% |
| 多客户端 | 同一 run_id 支持多个并发 WebSocket 连接 | ≥5 |

#### 3.3.3 触发条件

- 前端通过 WS URL `/ws/test-run/{run_id}` 连接
- TestRunner 执行过程中触发各回调钩子

#### 3.3.4 业务规则

**WsTestCallback（callbacks.py）**：

| 钩子 | WS 消息 type | 携带数据 |
|------|:--:|------|
| `on_log` | `log` | {message, timestamp} |
| `on_case_started` | `case_started` | {case_id, case_title, total_iterations} |
| `on_iteration_result` | `iteration_result` | {case_id, iteration, result, duration_ms, detail} |
| `on_case_finished` | `case_finished` | {case_id, pass, fail, rate} |
| `on_run_finished` | `run_finished` | {total_pass, total_fail, duration, csv_path, log_path} |
| `on_device_error` | `device_error` | {error_message} |

**架构**：WsTestCallback 维护 `clients: dict[str, set]`（按 run_id 分组的消费者集合），通过 `_broadcast` 向所有订阅者推送 JSON 消息。

#### 3.3.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| WS 连接 | onMounted 时连接 `ws://localhost:8765/ws/test-run/{run_id}`，onUnmounted 断开 |
| 消息处理 | 根据 type 分发：log→追加日志 / iteration_result→更新进度 / case_finished→更新统计 / run_finished→启用按钮+显示结果 |
| 断线重连 | 同 element-locator 的 WS 策略（3s 行重连，最多 5 次） |

#### 3.3.6 后端接口要求

| 接口 | 核心行为 |
|------|---------|
| WebSocket `/ws/test-run/{run_id}` | TestRunConsumer 注册到 test_callbacks，接收执行事件推送。详见附录 §4.3 |

---

### 3.4 F-04：执行控制

#### 3.4.1 需求定义

支持循环执行（loop_count）、执行过程中途停止、多设备并行执行、查询执行历史和当前状态。

#### 3.4.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 循环控制精度 | 中断时当前迭代完成后 ≤1s 停止 | ≤1s |
| 并行执行容量 | 同时运行的测试任务数 | ≥3 |

#### 3.4.3 触发条件

- 用户设置 loop_count > 1 后点击执行
- 用户点击「停止」按钮
- 用户查询执行历史

#### 3.4.4 业务规则

**停止机制**：
```
POST /api/runner/run/{run_id}/stop
  → 调用 stop_run(run_id)
  → 设置 _active_runs[run_id].is_running = False
  → StepExecutor 中每 100ms 检查 is_running
  → 当前步骤标记为 'stopped'
  → 清理资源，记录日志
```

**循环机制**：
```
FOR i IN range(loop_count):
    result = executor.execute_all(case.steps_data)
    记录 iteration_result
    if not is_running: break
```

**并行机制**：每个 TestRunner 持有独立的 DeviceAdapter，通过 device-pool 的锁机制保证同一设备同时只有 1 个运行器在操作。不同设备可以并行执行。

#### 3.4.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| 停止按钮 | 执行中显示红色"停止"按钮，点击后 disabled + "停止中..." |
| 停止反馈 | 收到 run_finished 事件后恢复按钮状态 |
| 执行历史 | 从 `GET /api/runner/runs` 加载历史列表 |

#### 3.4.6 后端接口要求

| 接口 | 核心行为 |
|------|---------|
| `POST /api/runner/run/{run_id}/stop` | 设置 is_running=False。详见附录 §4.3.2 |
| `GET /api/runner/run/{run_id}/status` | 获取运行状态 + 聚合统计。详见附录 §4.3.3 |
| `GET /api/runner/runs` | 列出所有执行记录（历史）。详见附录 §4.3.4 |

---

## 4. 附录

### 4.1 数据模型

#### 4.1.1 tr_test_runs（测试执行记录）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BigAutoField | PK | 自增主键 |
| `run_id` | CharField(200) | UNIQUE | 运行唯一标识（时间戳生成） |
| `status` | CharField(50) | default='PENDING' | PENDING / RUNNING / STOPPED / COMPLETED |
| `device_serial` | CharField(200) | — | 执行设备序列号 |
| `selected_cases` | JSONField | default=list | 选中的用例 ID 列表 |
| `loop_count` | IntegerField | default=1 | 每用例循环次数 |
| `summary` | JSONField | default=dict | 运行摘要（pass/fail/total） |
| `started_at` | CharField(100) | — | 开始时间 ISO 字符串 |
| `finished_at` | CharField(100) | — | 结束时间 ISO 字符串 |
| `csv_path` | CharField(1000) | — | CSV 报告路径 |
| `log_path` | CharField(1000) | — | 日志文件路径 |

#### 4.1.2 tr_test_results（单次迭代结果）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BigAutoField | PK | 自增主键 |
| `run` | FK(TestRunRecord) | CASCADE | 所属运行 |
| `case_id` | CharField(200) | INDEX | 用例 ID |
| `iteration` | IntegerField | — | 第几轮迭代 |
| `result` | CharField(50) | INDEX | pass / fail / stopped |
| `duration_ms` | FloatField | — | 本轮耗时（毫秒） |
| `detail` | TextField | — | 失败详情 |

---

### 4.2 状态机

```
TestRunRecord.status:
  PENDING ──→ RUNNING ──┬──→ COMPLETED
                         │
                         └──→ STOPPED
```

| 转换 | 触发事件 | 前置条件 | 副作用 |
|------|----------|----------|--------|
| PENDING → RUNNING | asyncio.create_task 启动 | 用例已加载 | 更新 started_at |
| RUNNING → COMPLETED | 所有用例执行完毕 | is_running=True | 生成报告 + callback.on_run_finished |
| RUNNING → STOPPED | stop_run() 被调用 | is_running=True | 标记 stopped + 清理 |

---

### 4.3 API 接口规格

| # | 方法 | 路径 | 功能 |
|---|------|------|------|
| 1 | POST | `/api/runner/run` | 启动异步测试执行 |
| 2 | POST | `/api/runner/run/{run_id}/stop` | 停止执行 |
| 3 | GET | `/api/runner/run/{run_id}/status` | 查询运行状态 |
| 4 | GET | `/api/runner/runs` | 执行历史列表 |
| — | WS | `/ws/test-run/{run_id}` | 实时执行事件推送 |

**POST /api/runner/run** (启动执行)

Request:
```json
{
  "case_ids": ["login_test", "order_test"],
  "loop_count": 3,
  "device_serial": "RF8N21MSW7A"
}
```

Response 200:
```json
{
  "ok": true,
  "run_id": "20260630_153000",
  "ws_url": "/ws/test-run/20260630_153000",
  "total_cases": 2,
  "total_iterations": 6
}
```

**GET /api/runner/run/{run_id}/status** (查询状态)

Response 200 (活跃运行):
```json
{
  "ok": true,
  "run_id": "20260630_153000",
  "status": "RUNNING",
  "progress": {"current_case": 1, "total_cases": 2, "current_iteration": 2, "total_iterations": 6},
  "results": {"pass": 5, "fail": 0, "stopped": 0}
}
```

Response 200 (已完成):
```json
{
  "ok": true,
  "run_id": "20260630_153000",
  "status": "COMPLETED",
  "summary": {"total_pass": 6, "total_fail": 0, "total_error": 0, "duration": 45.2},
  "csv_path": "logs/result_20260630_153000.csv",
  "log_path": "logs/test_20260630_153000.log"
}
```

---

### 4.4 非功能需求

| 类别 | 指标 | 目标值 |
|------|------|:--:|
| **性能** | 单步骤响应 | ≤3s（含设备操作） |
| **性能** | 执行启动响应 | ≤300ms |
| **性能** | WS 推送延迟 | ≤200ms |
| **并发** | 并行执行任务数 | ≥3 |
| **可靠性** | 步骤超时不阻塞 | 超时立即返回 fail，继续下一步 |
| **可靠性** | 设备断连自动释放锁 | 100% |

---

### 4.5 非目标（Non-goals）

| 功能 | 原因 | 归属 |
|------|------|------|
| 分布式执行（多主机） | 当前单主机设计 | v4 |
| 定时执行 | project-hub v3 | scheduler |
| 条件分支/循环执行 | 当前为顺序执行 | v4 |
| 数据驱动（CSV 参数化） | v3 规划 | v3 |
| 执行失败自动重试 | 当前手动停止 + 重来 | v3 |

---

### 4.6 里程碑

| 阶段 | 交付物 | 对应功能 |
|------|------|----------|
| v1 ✅ | 异步执行 + 14 种步骤引擎 + WS 推送 + 停止 | F-01, F-02, F-03, F-04 |
| v2 当前 | 多设备并行 + 执行历史 + 失败截屏 | 增强 |
| v3 | 数据驱动 + 条件分支 + 执行失败自动重试 | — |

---

## 变更记录

| 版本 | 日期 | 变更类型 | 变更摘要 |
|------|------|----------|----------|
| v1.0 | 2026-06-30 | — | v1 实现完成：异步执行 + 14 种步骤 + WS |
| v2.0 | 2026-06-30 | 重写 | 统一 6 维度结构，补充执行架构和步骤逻辑 |
