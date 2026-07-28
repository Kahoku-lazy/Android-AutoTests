# PRD-09：执行引擎重构 — 统一调度器 + YAML 驱动执行

> **状态：** SPEC 阶段 | **优先级：** P0 | **预估工期：** 2-3 周

---

## 一、背景

当前执行引擎在原有 Android UI 自动化的基础上，新增了 API 测试和 Web 自动化两个执行器。但架构存在五个根深问题：

| # | 问题 | 影响 |
|---|------|------|
| 1 | 三个 Runner 零共享代码，各自实现心跳/迭代/回调 | 修一个 bug 要改 3 处，调 2h 无结果 |
| 2 | 调度逻辑散落在 4 个文件中，上帝函数 `_execute_tests` 376 行 | 新增一种任务类型要改 5 个文件 |
| 3 | API/Web 执行后无报告文件产出（只有 UI 调了 `ReportGenerator`） | API/Web 执行完查不到日志 |
| 4 | API/Web 零预校验（Android 有 5 步设备预检） | URL 不可达到执行时才发现，"用例能建不能跑" |
| 5 | 前端设备状态 30s 轮询，排队位置不可见，无全局调度视图 | 用户不知道任务何时开始 |

---

## 二、目标

### 2.1 核心目标

**统一调度器** — 三种任务类型走同一套排队/并发/状态管理逻辑。

**YAML 驱动执行** — UI / API / Web 三种用例统一以 YAML 格式输出和加载，执行器从 YAML 文件读取后执行。YAML 是唯一用例定义格式（不再依赖 DB 的 JSON 字段）。

**全链路闭环** — 每个任务：预校验 → 排队 → 执行 → 报告 → 通知，缺一不可。

### 2.2 并行策略

| 任务类型 | 资源模型 | 并行策略 |
|---------|---------|---------|
| UI Automation | 物理 Android 设备 | 单设备串行（max=1/device），多设备并行 |
| API Testing | 无外部依赖，纯 HTTP | 全局并行池，max_concurrent=10 |
| Web Automation | Playwright headless Chromium (~150MB/实例) | 全局并行池，max_concurrent=3 |

---

## 三、YAML 统一用例格式

### 3.1 设计原则

- YAML 是**唯一用例定义格式**，替代当前 DB 中 `steps_json` (JSON TextField) 的碎片化存储
- 所有用例类型（UI / API / Web）共用统一的 YAML schema
- 用例导出 → YAML 文件；执行器加载 → YAML 文件
- YAML 文件存储在 `exports/` 目录，按类型分子目录

### 3.2 UI 自动化 YAML

```yaml
# exports/ui/android_login.yaml
schema: "testcase-v2"
name: "登录流程测试"
task_type: ui_automation
device:
  package_name: "com.example.app"
  min_sdk: 26
watchers:
  - xpath: "//*[@text='允许']"
    action: click
  - xpath: "//*[@text='确定']"
    action: click
steps:
  - type: wait
    xpath: "//*[@resource-id='com.example:id/username']"
    timeout: 10
    description: "等待用户名输入框"
  - type: click
    xpath: "//*[@resource-id='com.example:id/username']"
    description: "点击用户名输入框"
  - type: sleep
    timeout: 0.5
  - type: start_app
    xpath: "com.example.app"
  - type: verify_text
    xpath: "//*[@resource-id='com.example:id/welcome']"
    expected_text: "欢迎"
  - type: loop_n
    index: 3
    description: "重复点击 3 次"
    children:
      - type: click
        xpath: "//*[@text='下一步']"
  - type: if_element_appear
    xpath: "//*[@text='广告']"
    children:
      - type: click
        xpath: "//*[@text='关闭']"
```

### 3.3 API 测试 YAML

```yaml
# exports/api/user_api.yaml
schema: "testcase-v2"
name: "用户 CRUD 接口测试"
task_type: api_testing
base_url: "https://api.example.com"
headers:
  Content-Type: "application/json"
  Authorization: "Bearer {{token}}"
steps:
  - type: api_request
    method: POST
    url: "/v1/login"
    body:
      username: "admin"
      password: "123456"
    extract:
      token: "$.data.token"
      user_id: "$.data.user.id"
    expected_status: 200
  - type: api_request
    method: GET
    url: "/v1/users/{{user_id}}"
    expected_status: 200
    assertions:
      - path: "$.data.username"
        op: equals
        expect: "admin"
  - type: api_assert
    assertions:
      - path: "$.data.status"
        op: equals
        expect: "active"
  - type: api_sleep
    timeout: 2
  - type: api_log
    description: "所有用户接口测试通过"
```

### 3.4 Web 自动化 YAML

```yaml
# exports/web/login_flow.yaml
schema: "testcase-v2"
name: "Web 登录流程"
task_type: web_automation
start_url: "https://example.com/login"
viewport:
  width: 1280
  height: 720
watchers:
  - selector: ".cookie-banner .accept"
    action: click
  - selector: ".modal-close"
    action: click
steps:
  - type: web_navigate
    url: "https://example.com/login"
  - type: web_wait
    selector: "#login-form"
    timeout: 10
  - type: web_fill
    selector: "#username"
    value: "admin"
  - type: web_fill
    selector: "#password"
    value: "123456"
  - type: web_click
    selector: "#login-btn"
  - type: web_wait
    selector: ".dashboard"
    timeout: 10
  - type: web_assert
    expected_text: "欢迎回来"
  - type: web_screenshot
    description: "登录成功截图"
```

---

## 四、架构设计

### 4.1 模块结构

```
apps/test_runner/
├── scheduler.py          # NEW: 统一调度器（Base + Device/Api/Web 子类）
├── case_validator.py     # NEW: 执行前用例校验器
├── yaml_loader.py        # NEW: YAML 加载器（统一入口）
├── yaml_exporter.py      # NEW: YAML 导出器（统一出口）
├── runner.py             # REFACTOR: 提取 BaseRunner
├── remote_runner.py      # REFACTOR: 合并 API/Web
├── executor.py           # KEEP: StepExecutor (UI)
├── api_executor.py       # REFACTOR: async
├── api_adapter.py        # REFACTOR: 删除 legacy path
├── web_executor.py       # KEEP: WebExecutor
├── web_adapter.py        # REFACTOR: 统一接口
├── adapter.py            # REFACTOR: 提取 BaseAdapter
├── callbacks.py          # EXTEND: 新增调度器状态回调
├── consumers.py          # EXTEND: 新增 SchedulerStatusConsumer + DeviceStatusConsumer
├── state_machine.py      # KEEP
├── views/
│   ├── execution.py      # SIMPLIFY: 调度逻辑委托给 Scheduler
│   ├── executor.py       # SIMPLIFY: _execute_tests 移入 Scheduler
│   └── helpers.py        # SIMPLIFY: 队列移出
```

### 4.2 核心类关系

```
                    ┌─────────────────────┐
                    │    CaseValidator     │  执行前校验
                    │  - validate_api()   │
                    │  - validate_web()   │
                    │  - validate_ui()    │
                    └──────────┬──────────┘
                               │ uses
                               v
┌──────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│ YAMLLoader   │────>│    BaseScheduler     │────>│   ReportGenerator │
│ - load_case()│     │  - submit(spec)      │     │   (统一调用)       │
│ - load_batch │     │  - _pipeline(spec)   │     └──────────────────┘
└──────────────┘     │  - status -> Status   │
                     │  - max_concurrent     │
                     └──────────┬───────────┘
                                │ inherits
              ┌─────────────────┼─────────────────┐
              v                 v                 v
   ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
   │ DeviceScheduler  │ │ ApiScheduler │ │  WebScheduler    │
   │ max_concurrent=1 │ │ max=10       │ │  max=3           │
   │ per serial       │ │ global pool  │ │  global pool     │
   └────────┬─────────┘ └──────┬───────┘ └────────┬─────────┘
            v                  v                   v
   ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
   │    TestRunner    │ │ RemoteRunner │ │  RemoteRunner    │
   │  (BaseRunner)    │ │ (BaseRunner) │ │  (BaseRunner)    │
   └──────────────────┘ └──────────────┘ └──────────────────┘
```

### 4.3 执行全流程（统一管道）

```
1. start_test_run() HTTP 入口
   │
2. YAMLLoader.load_batch(case_paths)  ← 从 YAML 文件加载用例
   │
3. CaseValidator.validate(task_type, cases)  ← 预校验
   │  ├─ UI: ADB → u2.connect → display_info (已有)
   │  ├─ API: URL 可达性 (HEAD), method 合法性, headers 格式
   │  └─ Web: URL 可达性, Playwright 安装检测
   │
4. Scheduler.submit(task_spec)
   │  ├─ 有空闲槽位 → 立即执行
   │  └─ 无空闲槽位 → 进入队列，WS 推送排队位置
   │
5. _execute_pipeline(spec)  ← 统一的执行管道
   │  ├─ 状态机: idle → queued → running
   │  ├─ runner.run()
   │  ├─ 结果持久化 (TestRunRecord + TestResult)
   │  ├─ ReportGenerator.save_log() + save_csv()  ← 所有类型统一
   │  └─ 状态机: running → done (complete/fail/stopped)
   │
6. Scheduler._on_task_finished(spec)
   │  ├─ 释放槽位
   │  ├─ WS 推送状态更新
   │  └─ 从队列取出下一个任务
   │
7. 前端组件响应 WS 事件
   ├─ TaskCard: 任务状态 + 排队位置 + 执行进度
   ├─ DevicePanel: 设备 ONLINE/BUSY 实时切换
   └─ SchedulerStats: 各类型运行/排队/可用槽位
```

---

## 五、验收条件

### AC-1：YAML 统一格式
- [ ] UI / API / Web 三种用例均可导出为标准 YAML 文件
- [ ] `YAMLLoader` 可从 YAML 文件加载任意类型用例为 `TestCaseDef`
- [ ] YAML 导出内容与原始用例步骤一致，无信息丢失
- [ ] `POST /api/cases/{type}/export/yaml` 三端点均可工作

### AC-2：统一调度器
- [ ] `BaseScheduler` 控制并发上限（Semaphore）
- [ ] `DeviceScheduler` 单设备串行，多设备并行
- [ ] `ApiScheduler` 全局上限 10，超限排队
- [ ] `WebScheduler` 全局上限 3，超限排队
- [ ] 排队任务在设备释放后自动启动
- [ ] Scheduler 状态可通过 `Scheduler.status` 查询

### AC-3：用例预校验
- [ ] API 用例 URL 不可达时，预校验失败，不进入执行
- [ ] Web 用例 Playwright 未安装时，预校验失败
- [ ] UI 用例设备不可用时，预校验失败（保持现有行为）
- [ ] 校验失败返回具体原因（如 "URL https://bad-url 不可达: Connection refused"）

### AC-4：测试报告
- [ ] API 任务执行完毕生成 `.log` + `.csv` 报告文件
- [ ] Web 任务执行完毕生成 `.log` + `.csv` 报告文件
- [ ] UI 任务执行完毕生成报告（保持现有行为）
- [ ] `rg_reports` 表有记录

### AC-5：前端实时状态
- [ ] 设备状态变更实时推送（BUSY ↔ ONLINE），延迟 < 2s
- [ ] 排队任务显示排队位置
- [ ] SchedulerStats 状态栏显示全局运行/排队/可用槽位
- [ ] WS 断连自动降级为 5s HTTP 轮询

---

## 六、任务拆解

### Sprint 1：基础设施（3-4 天）

**T1.1** 安装 PyYAML，创建 `yaml_loader.py` + `yaml_exporter.py`
- `YAMLLoader.load_case(path) -> TestCaseDef`
- `YAMLLoader.load_batch(paths) -> list[TestCaseDef]`
- `YAMLExporter.export(test_case: TestCaseDef) -> str`
- 三种类型的 YAML 序列化/反序列化

**T1.2** 提取 `BaseAdapter`
- `apps/test_runner/adapter.py` 新增 `BaseAdapter` 抽象类
- `DeviceAdapter` / `ApiAdapter` / `WebAdapter` 继承 `BaseAdapter`
- `ApiAdapter` 删除 `execute_case(dict)` legacy 路径

**T1.3** 提取 `BaseRunner`
- `apps/test_runner/runner.py` 新增 `BaseRunner` 基类
- 提取公共方法：`_heartbeat` / `_record_case_result` / `_sync_log`
- `TestRunner(BaseRunner)` — 保持现有逻辑
- `RemoteTestRunner(BaseRunner)` — 消除 `is_async_executor` 标志

### Sprint 2：调度器核心（3-4 天）

**T2.1** 创建 `scheduler.py` — `BaseScheduler`
- `TaskSpec` 统一任务描述数据结构
- `BaseScheduler.submit(spec)` / `_execute_pipeline(spec)`
- `asyncio.Semaphore` 并发控制
- `SchedulerStatus` 数据结构

**T2.2** 创建三个子类 Scheduler
- `DeviceScheduler(max_concurrent=1)` — 每 serial 一个实例
- `ApiScheduler(max_concurrent=10)` — 全局单例
- `WebScheduler(max_concurrent=3)` — 全局单例

**T2.3** 迁移 `_execute_tests` → `BaseScheduler._execute_pipeline`
- 从 `views/executor.py` 提取核心管道
- 统一报告生成：所有类型调 `ReportGenerator.save_log()` + `save_csv()`
- 队列逻辑从 `views/helpers.py` 移入 `DeviceScheduler`

**T2.4** 重写 `start_test_run`
- 接入 `YAMLLoader` → `CaseValidator` → `Scheduler.submit`
- 删除旧的三路分支（UI/API/Web 各自启动逻辑）

### Sprint 3：校验 + 报告（2-3 天）

**T3.1** 创建 `case_validator.py`
- `CaseValidator.validate(task_type, cases) -> ValidationReport`
- UI: 复用 `check_and_connect_async`（已有）
- API: URL HEAD 请求可达性检查（5s 超时）
- Web: URL 可达性 + Playwright 安装检测

**T3.2** 统一报告生成
- `ReportGenerator.save_log()` 在 `_execute_pipeline` 的 finalize 阶段统一调用
- 新增 `save_csv()` 导出
- 确保 `rg_reports` 表有记录

**T3.3** 三种类型的 YAML 导出端点
- `POST /api/cases/export/yaml` (UI) — 已有
- `POST /api/cases/api-testing/export/yaml` (API) — 新增
- `POST /api/cases/web/export/yaml` (Web) — 新增

### Sprint 4：前端实时状态（3-4 天）

**T4.1** 后端 WebSocket 扩展
- `SchedulerStatusConsumer` (ws://.../scheduler/status)
  - 事件：`scheduler_snapshot`, `task_queued`, `task_started`, `task_finished`
- `DeviceStatusConsumer` (ws://.../devices/status)
  - 事件：`device_snapshot`, `device_status_change`
- `gateway/routing.py` 注册新路由
- Scheduler 在状态变更时广播

**T4.2** 前端 composable
- `useSchedulerStatus.js` — 全局单例 WS 连接
- 替换 `useQueuePoller.js` HTTP 轮询为 WS 推送

**T4.3** 前端组件
- `SchedulerStats.vue` — 顶部状态栏
- `TaskCard` 增强 — 排队位置显示
- `NewTaskDialog` 增强 — YAML 用例选择/上传替代 DB 用例选择
- 设备选择器 — 实时 BUSY/ONLINE 状态

### Sprint 5：Web 用例编辑器适配（2 天）

**T5.1** Web 用例编辑改为 Android 同级结构
- Web 用例编辑：先写 UI 操作步骤，后导出 YAML
- 类比 Android：元素定位 → 页面流 → 导出 YAML → 执行

**T5.2** WebEditor 改造
- 步骤编辑器（可视化添加 web_navigate/web_click/web_fill 等）
- 实时预览 YAML 输出
- 导出按钮 → 保存 YAML 到 exports/web/

---

## 七、技术决策记录

| 决策 | 选项 | 选择 | 原因 |
|------|------|:--:|------|
| YAML 库 | PyYAML vs ruamel.yaml | PyYAML | 轻量，项目已有手写 YAML dump，只需补齐 load |
| 并发控制 | Semaphore vs BoundedSemaphore vs 自定义 | `asyncio.Semaphore` | 标准库，无额外依赖 |
| Runner 抽象 | ABC 抽象类 vs Duck typing | ABC | 明确契约，IDE 支持 |
| 报告生成位置 | Runner 内 vs Scheduler 内 | Scheduler 内 | 所有 Runner 共享，单一职责 |
| WS 频道设计 | 单频道复用 vs 多频道分离 | 多频道分离 | scheduler/status + devices/status 独立订阅 |

---

## 八、风险

| 风险 | 概率 | 缓解措施 |
|------|:--:|------|
| 重构破坏现有 UI 用例执行 | 中 | `TestRunner` 保持接口不变，只提取基类 |
| _device_executor 4 线程上限成为瓶颈 | 低 | 当前设备数量有限；将来可配置化 |
| Playwright 并发 3 实例内存不足 | 低 | headless 模式 ~150MB/实例，3 实例 ~450MB |
| YAML 迁移时 DB 中历史数据不兼容 | 中 | 提供 DB→YAML 迁移脚本 `tools/migrate_cases_to_yaml.py` |
