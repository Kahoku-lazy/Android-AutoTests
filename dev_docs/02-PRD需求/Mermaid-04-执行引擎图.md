# Mermaid-04 — 执行引擎架构图

> 关联：[PRD-04-执行引擎](./PRD-04-执行引擎.md) · [PRD-04-执行引擎-业务功能](./PRD-04-执行引擎-业务功能.md) · [API-04-执行引擎-接口文档](./API-04-执行引擎-接口文档.md)
> 版本：v2.0 · 日期：2026-07-29

---

## 一、架构全景图

> 从上到下四层：前端 → API 网关 → 业务核心 → 外部目标。

```mermaid
flowchart TD
    U["👤 用户浏览器<br/>Vue 3 前端应用"]

    U -->|"HTTP REST"| GATEWAY["API 网关层<br/>/api/runner/*（13 端点）<br/>/api/reports/*（6 端点）"]
    U -->|"WebSocket"| GATEWAY

    GATEWAY --> L1["① 视图层 · HTTP 入口<br/>解析请求 → 调服务层 → 返回 JSON"]
    GATEWAY --> L1_WS["① WebSocket 入口<br/>TestRunConsumer<br/>TREP v1.0 协议"]

    L1 --> L2["② 服务层<br/>状态机（唯一真相源）· 调度器（并发控制）· 任务 API"]

    L2 --> L3["③ 执行核心<br/>TestRunner（UI）· RemoteTestRunner（API/Web）"]

    L3 --> L4["④ 适配器层"]
    L4 --> T1["📱 Android 设备<br/>ADB + u2 + Airtest"]
    L4 --> T2["🌐 浏览器<br/>Playwright Chromium"]
    L4 --> T3["🔗 HTTP 端点<br/>被测 API 服务"]

    L1_WS -.->|"实时推送<br/>10 种事件"| U

    L2 --> DB[("🗄 数据库<br/>tr_task_cards<br/>tr_test_runs<br/>tr_test_results")]

    style U fill:#e3f2fd,stroke:#2196f3
    style GATEWAY fill:#fff3e0,stroke:#ff9800
    style L1 fill:#e8f5e9,stroke:#4caf50
    style L1_WS fill:#f3e5f5,stroke:#9c27b0
    style L2 fill:#e8eaf6,stroke:#3f51b5
    style L3 fill:#fff8e1,stroke:#ffc107
    style L4 fill:#fce4ec,stroke:#e91e63
    style DB fill:#f5f5f5,stroke:#999
    style T1 fill:#e8f5e9,stroke:#4caf50
    style T2 fill:#e3f2fd,stroke:#2196f3
    style T3 fill:#fff3e0,stroke:#ff9800
```

### 各层职责

| 层 | 一句话职责 | 关键组件 |
|:--:|------|------|
| ① 视图层 | 接收 HTTP/WS 请求，调服务层，返回 JSON | 13 个 Django View + 1 个 WS Consumer |
| ② 服务层 | 状态转移 + 并发调度 + 写操作收敛 | 状态机 / 调度器注册表 / api.py |
| ③ 执行核心 | 编排测试生命周期，分发步骤到适配器 | TestRunner（UI）/ RemoteTestRunner（API, Web） |
| ④ 适配器层 | 封装设备/浏览器/HTTP 操作细节 | DeviceAdapter / WebAdapter / ApiAdapter |

### 两条数据通道

| 通道 | 路径 | 用途 |
|------|------|------|
| **HTTP 请求-响应** | 前端 → API 网关 → 视图层 → 服务层 → 执行核心 | 创建任务、启停执行、查询状态 |
| **WebSocket 实时推送** | 执行核心 → WS Consumer → 前端 | 步骤进度、日志、心跳（执行期间持续推送） |

---

## 二、核心类图

> 分三组展示：调度器继承链 → Runner-Executor-Adapter 组合链 → 状态机与持久化。

### 2.1 调度器继承链

```mermaid
classDiagram
    direction TB

    class BaseScheduler {
        -Semaphore 信号量
        -list 等待队列
        +submit(任务) 提交
        +stop(运行ID) 停止
        #_make_runner()* 工厂方法
        #_try_dequeue() 出队
    }

    class DeviceScheduler {
        +max_concurrent = 1
        每台设备一个实例
    }

    class ApiScheduler {
        +max_concurrent = 10
    }

    class WebScheduler {
        +max_concurrent = 3
    }

    class SchedulerRegistry {
        +get(任务类型, 设备) 获取调度器
    }

    BaseScheduler <|-- DeviceScheduler : 继承
    BaseScheduler <|-- ApiScheduler : 继承
    BaseScheduler <|-- WebScheduler : 继承
    SchedulerRegistry --> BaseScheduler : 管理
```

**模式**：模板方法。`BaseScheduler` 定义调度框架（提交→获取信号量→执行→finally释放→出队），三个子类只覆写 `_make_runner()` 工厂方法和 `max_concurrent`。

### 2.2 Runner - Executor - Adapter 组合链

```mermaid
classDiagram
    direction LR

    class TestRunner {
        +run(用例列表) 运行结果
        -_execute_iteration_with_retry() 带重试
        -_wire_step_callbacks() 绑定回调
    }

    class RemoteTestRunner {
        +run(用例列表) 运行结果
        -_run_single_case() 单用例
        -_wire_step_callbacks() 绑定回调
    }

    class StepExecutor {
        +execute_all(步骤列表) 结果
        24 种 UI 步骤分发
    }

    class ApiExecutor {
        +execute_case(用例) 结果
        变量提取 + 数据驱动
    }

    class WebExecutor {
        +execute_case(用例) 结果
        异步 + 截图标注
    }

    class DeviceAdapter {
        封装 u2 + Airtest
    }

    class ApiAdapter {
        封装 requests
    }

    class WebAdapter {
        封装 Playwright
    }

    TestRunner --> StepExecutor : 创建
    TestRunner --> DeviceAdapter : 创建
    RemoteTestRunner --> ApiExecutor : 创建
    RemoteTestRunner --> ApiAdapter : 创建
    RemoteTestRunner --> WebExecutor : 创建
    RemoteTestRunner --> WebAdapter : 创建
    StepExecutor --> DeviceAdapter : 操作
    ApiExecutor --> ApiAdapter : 操作
    WebExecutor --> WebAdapter : 操作
```

**多态**：`TestRunner`（UI 真机）与 `RemoteTestRunner`（API/Web 虚拟设备）暴露相同接口，编排器 `_execute_tests()` 不感知差异。

### 2.3 状态机与持久化

```mermaid
classDiagram
    direction TB

    class 状态机 {
        <<static>>
        +入队(任务卡片)
        +取消(任务卡片)
        +出队(任务卡片) 运行记录
        +完成(任务卡片, 运行记录)
        +失败(任务卡片, 运行记录, 原因)
        +记录迭代(运行记录, 结果)
        +恢复孤儿()
    }

    class 任务卡片 {
        task_id 主键
        status 状态
        outcome 终态结果
        case_items 用例快照
        failed_steps 失败步骤
        run → 运行记录
    }

    class 运行记录 {
        run_id 唯一标识
        selected_cases 用例快照
        summary 通过率汇总
        started_at 启动时间
        finished_at 结束时间
    }

    class 测试结果 {
        case_id 用例标识
        iteration 迭代序号
        result 结果
        duration_ms 耗时
        step_details 步骤详情
    }

    状态机 --> 任务卡片 : 写入
    状态机 --> 运行记录 : 写入
    状态机 --> 测试结果 : 写入
    任务卡片 --> 运行记录 : run FK
    运行记录 --> 测试结果 : results FK
```

**关键约束**：所有状态变更经状态机，DB 事务 + 行级锁保证原子性，终态禁止再转移。

---

## 三、模块包图

> 箭头方向 = import 方向。只展示模块间的依赖关系，不逐文件列举。

```mermaid
flowchart TD
    subgraph FRONTEND["前端 (Vue)"]
        F_TEST["test-runner 模块<br/>主页面 + 详情页 + 弹窗"]
        F_REPORT["report-generator 模块<br/>报告列表 + 报告详情"]
    end

    subgraph VIEWS["Django 视图层"]
        V_RUNNER["test_runner/views/<br/>执行控制 + 任务 CRUD + 监控"]
        V_REPORT["report_generator/views/<br/>报告列表 + 运行报告 + 任务报告"]
    end

    subgraph SERVICE["服务层"]
        S_SM["state_machine.py<br/>状态机"]
        S_SCHED["scheduler.py<br/>调度器"]
        S_API["api.py<br/>写操作白名单"]
    end

    subgraph CORE["执行核心（内部实现）"]
        C_RUNNER["runner.py<br/>remote_runner.py"]
        C_EXEC["executors/ui/<br/>executors/api/<br/>executors/web/"]
    end

    subgraph MODELS["数据层"]
        M_ORM["models.py<br/>任务卡片 / 运行记录 / 测试结果"]
        M_TEST["models/test_models.py<br/>内存运行时模型"]
    end

    subgraph EXTERNAL["外部依赖"]
        E_DP["device_pool/api.py<br/>设备锁定与释放"]
        E_CM["case_manager/api.py<br/>用例定义查询"]
    end

    %% 前端 → 后端
    F_TEST -->|"HTTP / WS"| V_RUNNER
    F_REPORT -->|"HTTP"| V_REPORT

    %% 视图 → 服务
    V_RUNNER --> S_SM
    V_RUNNER --> S_SCHED
    V_RUNNER --> S_API
    V_REPORT --> M_ORM

    %% 服务 → 核心（通过工厂，非直接 import）
    S_SCHED -.->|"工厂模式创建"| C_RUNNER
    S_SCHED -.->|"工厂模式创建"| C_EXEC

    %% 核心 → 外部
    C_EXEC -->|"合法跨 App import"| E_DP
    V_RUNNER -->|"合法跨 App import"| E_CM

    %% 数据层被所有层读取
    V_RUNNER --> M_ORM
    S_SM --> M_ORM
    S_API --> M_ORM
    C_RUNNER --> M_TEST
    C_EXEC --> M_TEST

    %% 样式
    style FRONTEND fill:#e3f2fd,stroke:#2196f3
    style VIEWS fill:#e8f5e9,stroke:#4caf50
    style SERVICE fill:#e8eaf6,stroke:#3f51b5
    style CORE fill:#fce4ec,stroke:#e91e63
    style MODELS fill:#f5f5f5,stroke:#999
    style EXTERNAL fill:#fff3e0,stroke:#ff9800
```

### 防火墙规则

```
视图层 ──✅ import──→ 服务层（state_machine / api.py / scheduler）
视图层 ──❌ import──→ 执行核心（runner / executor）  ← 禁止！由调度器工厂间接创建

服务层 ──✅ import──→ 数据层（models / test_models）
服务层 ──✅ import──→ 外部 App api.py（device_pool / case_manager）

执行核心 ──✅ import──→ 外部设备库（u2 / Playwright / requests）
执行核心 ──❌ 不 import──→ Django 视图 / 服务层  ← 单向依赖

数据层 ──✅ 被所有层 import（只读查询）
数据层 ──❌ 写操作必须走 api.py  ← 写收敛原则
```

### 模块间 import 方向总览

| 从 ↓ / 到 → | 前端 | 视图层 | 服务层 | 执行核心 | 数据层 | 外部 App |
|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 前端 | — | HTTP/WS | ❌ | ❌ | ❌ | ❌ |
| 视图层 | ❌ | — | ✅ | ❌ | ✅ | ✅ |
| 服务层 | ❌ | ❌ | — | 工厂间接 | ✅ | ✅ |
| 执行核心 | ❌ | ❌ | ❌ | — | ✅ | ✅ |
| 数据层 | ❌ | ❌ | ❌ | ❌ | — | — |

---

## 附录：三图对照

| 图 | 回答什么问题 | 适合谁看 |
|:--:|------|------|
| 一、架构全景图 | 系统分几层？数据怎么流动？依赖哪些外部系统？ | 新人入职、架构评审 |
| 二、核心类图 | 有哪些类？谁继承谁？谁组合谁？ | 开发人员、代码评审 |
| 三、模块包图 | 哪个模块能 import 哪个？边界在哪里？ | 开发人员、CI 边界检查 |
