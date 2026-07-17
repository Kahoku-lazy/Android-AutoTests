# AI 编程参考手册 — 从 PRD 需求提炼

> 从 11 份 PRD 文档（1 总 + 7 子 + 2 工作流 + README）提炼为 AI 编码可直接查阅的约束清单。
> 不做人类阅读叙事，只保留：数据契约 · 状态机 · 约束清单 · 错误模板 · 陷阱 · Non-goals。

---

## 一、模块速查

| 模块 | Django App | 前端路径 | 自有表 | API数 | WS |
|------|-----------|---------|--------|:--:|:--:|
| 设备管理 | `apps/device_pool/` | `modules/device-pool/` | `dp_devices` `dp_device_locks` `dp_device_queue` | 12 REST | — |
| 元素定位 | `apps/element_locator/` | `modules/element-locator/` | `el_pages` `el_elements` `el_page_flows` | 14 REST | 1 (`/ws/screenshot`) |
| 用例管理 | `apps/case_manager/` | `modules/case-manager/` | `cm_test_definitions` `cm_case_directories` | 10 REST | — |
| 执行引擎 | `apps/test_runner/` | `modules/test-runner/` | `tr_test_runs` `tr_test_results` `tr_task_cards` `tr_test_sop` | 12 REST | 1 (`/ws/test-run/{id}`) |
| 测试报告 | `apps/report_generator/` | `modules/report-generator/` | `rg_reports` `rg_report_templates` | 6 REST | — |
| AI 助手 | `apps/ai_assistant/` | `modules/ai-assistant/` | `ai_agents` `ai_tools` `ai_conversations` `ai_messages` `ai_tasks` `ai_execution_logs` | 37 REST | SSE |
| 工作流 | `apps/workflow/` | `modules/workflow/` | `wf_directories` `wf_documents` | 10 REST | — |
| 仪表盘 | `apps/dashboard/` | `modules/dashboard/` | **无**（纯聚合） | 4 REST | — |

---

## 二、跨模块数据契约

### 2.1 element-locator → case-manager

```
数据流：el_elements (is_test_point=True) + xpath_candidates
       → 前端 EventBus "add-step-to-case" 或步骤编辑器元素选取器
       → cm_test_definitions.steps_json[].xpath
```

| 约束 | 说明 |
|------|------|
| XPath 8 种策略按 `count` 升序 | `count=1` 最优（唯一定位），前端应默认选第一个 |
| 元素唯一约束 `(page_id, resource_id, bounds)` | upsert 逻辑依赖此约束 |
| 步骤编辑器元素选取器按页面分组搜索 | 搜索字段：`alias` `text_val` `resource_id` |

### 2.2 case-manager → test-runner

```
数据流：cm_test_definitions.steps_json
       → TestRunner.run() 加载 TestCaseDef
       → StepExecutor 按 type 分发 → DeviceAdapter (uiautomator2)
```

| 契约 | 值 |
|------|-----|
| `steps_json` 格式 | `[{type, xpath, xpath2, timeout, expected_text, index, description, direction, distance}]` |
| 执行快照 | `TestRunRecord.selected_cases` 在启动时复制 `{case_id, title, steps_data}` 完整快照 |
| FK 保护 | `tr_test_results.case` → SET_NULL on delete，删用例不删历史结果 |

### 2.3 test-runner → report-generator

```
数据流：TestRunner.run() 完成
       → ReportGenerator.save_csv(results, failure_details)
       → ReportGenerator.save_log(run_id, log_lines)
```

| 契约 | 值 |
|------|-----|
| 报告数据来源 | `tr_test_runs` + `tr_test_results`，DB 实时查询，不依赖预生成文件 |
| 报告列表聚合 | annotate `total/passed` → 计算 `failed/rate` |

### 2.4 workflow → case-manager → test-runner

```
数据流：wf_documents (doc_type=test_case, config.linkedCaseId)
       → 同步到 cm_test_definitions（复用现有 API）
       → 从头运行 POST /api/runner/run (case_ids=[linkedCaseId])
```

| 运行模式 | 是否需要 linkedCaseId | 数据源 | API |
|---------|:--:|------|-----|
| 单步运行 | ❌ | Blockly 当前步 → JSON | `POST /api/runner/run-step` |
| 从当前步运行 | ❌ | 画布步骤链切片 → 前端串行 `run-step` | `POST /api/runner/run-step` |
| 从头运行 | ✅ | `cm_test_definitions` 落库步骤 | `POST /api/runner/run` |

**关键规则**：
- 🔴 不新增工作流专用后端端点（复用现有 device/runner/case API）
- 🔴 不新增第二套用例存储（运行链路复用 `linkedCaseId` → 用例库）
- 🔴 从头运行前画布有未同步修改 → 阻断并提示（不静默跑脏数据）
- 🔴 `POST /api/runner/run` 不支持 `start_step_index`（MVP 用前端串行 `run-step`）

### 2.5 AI Assistant (AgentScope) → 各业务模块

```
数据流：AgentScope Tool.call()
       → 直接 import Django ORM/API（同进程，不走 HTTP）
       → 24 业务 Tool + 4 Plan Tool
```

| 🔴 铁律 | 说明 |
|---------|------|
| 跨模块写必须走 `api.py` | 禁止 Tool 内直接 `Model.objects.create()` |
| 读操作可直接 ORM | `Model.objects.filter()` 允许 |
| 不走 HTTP | Tool 直接 import，不通过 requests/httpx 调 Django |

### 2.6 dashboard → 各业务模块

```
数据流：GET /api/dashboard/stats/ → 跨模块 ORM 只读聚合
```

| 🔴 铁律 |
|---------|
| 禁止仪表盘直接写其他 App 的表 |
| 禁止前端硬编码统计数字 |
| 禁止 `import _active_runs`（防火墙 #1） |

---

## 三、状态机

### 3.1 设备状态（device-pool）

```
(不存在) ──adb scan──► ONLINE ◄──release/timeout──┐
                         │  ▲                       │
                   lock  │  │ timeout               │
                         ▼  │                       │
           ┌──────────► BUSY├───────────────────────┘
           │            │  ▲
           │ heartbeat  │  │ adb reconnect
           │ fail       │  │
           │            ▼  │
           │         OFFLINE
           │            │
           │ disconnect │
           │            ▼
           │      OFFLINE ──adb scan──► ONLINE
           │            ▲
           └─disconnect─┘
```

| # | 当前态 | 事件 | 目标态 | 前置条件 |
|---|--------|------|--------|----------|
| 1 | (新) | adb scan 发现 | ONLINE | adb devices 列表有该 serial |
| 2 | OFFLINE | adb scan 恢复 | ONLINE | 同上 |
| 3 | ONLINE | lock | BUSY | 无活跃锁 |
| 4 | BUSY | release | ONLINE | 锁持有者或管理员 |
| 5 | BUSY | timeout | ONLINE | elapsed > timeout_seconds |
| 6 | ONLINE | adb scan 未发现 | OFFLINE | 不在 adb 列表 |
| 7 | OFFLINE | disconnect | OFFLINE | — |
| 8 | ONLINE | disconnect | OFFLINE | — |
| 9 | BUSY | disconnect(admin) | OFFLINE | 管理员权限 |
| 10 | OFFLINE | adb scan 发现 | ONLINE | 在 adb 列表 |

**并发控制**：两处锁：
- `DevicePool._lock`（`threading.Lock`）— 保护 `_instances` dict
- `DevicePool._u2_lock` — 全局串行化所有 u2 操作

### 3.2 任务生命周期（test-runner）

```
                    ┌──────────────┐
                    │ idle（未执行）  │  status=idle, running=F
                    └──────┬───────┘
                           │ 点「执行」
                           ▼
                    ┌──────────────┐
                    │ 检查设备忙碌？  │
                    └──┬────────┬──┘
                 空闲   │        │  忙碌
                    ▼        ▼
           ┌──────────┐  ┌──────────┐
           │ running  │  │ queued   │  status=queued, running=F
           │ running=T│  └────┬─────┘
           └────┬─────┘       │ 取消排队
                │             ▼
       点「停止」│        ┌──────────┐
                │        │ idle     │  保留配置，可重新执行
                ▼        └──────────┘
           ┌──────────────────────┐
           │ done（status=done）   │
           │ outcome=completed    │  → ✅ 已完成
           │ outcome=stopped      │  → ⏹ 未完成（用户停止）
           │ outcome=interrupted  │  → ⚠️ 运行中断（服务器重启孤儿）
           │ outcome=error        │  → 💥 异常终止（设备异常/崩溃）
           └──────────────────────┘
```

| 🔴 关键规则 | 说明 |
|------------|------|
| `status` 管生命周期 | idle / queued / running / done（4 个值） |
| `outcome` 管终态细分 | 仅 `status=done` 时有意义：completed / stopped / interrupted / error |
| 两个字段必须同时检查 | 不能只判断 `status` 或只判断 `running` 布尔值 |
| 内存队列不持久化 | `_device_queue` 是内存结构，服务器重启丢失 |

### 3.3 AI SOP 四阶段（ai-assistant）

```
Phase 1: 需求分析 → Phase 2: 元素准备 → Phase 3: 用例创建调试 → Phase 4: 任务执行
```

| 阶段 | SOP 状态机操作 | 产出字段 |
|:--:|------|------|
| 1→2 | `create_test_sop` | `requirement` `case_design` |
| 2→3 | `update_test_sop` | `element_mapping` `element_gaps` |
| 3→4 | `update_test_sop` | `case_ids` `debug_notes` |
| 4→完成 | `update_test_sop(status='completed')` | `run_id` `run_results` |

**两层工具体系**：
- **Plan 工具**（TaskCreate/Get/List/Update）— `agent.state.tasks_context` 内存态，管"怎么做这个阶段"
- **SOP 工具**（create_test_sop/update_test_sop）— `tr_test_sop` DB 持久化，管"做到哪个阶段了"

### 3.4 工作流运行状态

```
idle ──选择设备──► ready ──从头/从当前/单步──► running ──完成/失败──► idle|ready
                     ▲                         │
                     └──────── 停止 ───────────┘
```

| 状态 | 工具栏 | 积木画布 |
|------|--------|---------|
| idle/ready | 可点运行；停止禁用 | 无高亮 |
| running | 运行类按钮禁用；停止可用 | 当前步高亮；已完成步成功/失败色 |
| 结束 | 恢复按钮；文案摘要 | 保留末态色 |

---

## 四、约束清单（按模块）

### 4.1 device-pool

| # | 约束 | 位置 | 严重 |
|:--:|------|:--:|:--:|
| 1 | 设备 serial 全局唯一 | `models.py` UNIQUE | 🔴 |
| 2 | 锁超时默认 300s | `api.py` 默认参数 | 🟠 |
| 3 | 设备锁记录永不删除（审计） | 标记 released/expired | 🟠 |
| 4 | 强制断开他人 BUSY 设备需管理员 | `views.py` | 🔴 |
| 5 | 排队 FIFO | `_device_queue` 列表 | 🟠 |
| 6 | 设备信息连接时采集（model/brand/resolution/version） | `views.py` connect | 🟡 |
| 7 | ADB 扫描：BUSY 设备不在 adb 列表时保持 BUSY | `_update_device_status()` | 🔴 |

### 4.2 case-manager

| # | 约束 | 位置 | 严重 |
|:--:|------|:--:|:--:|
| 1 | 目录最大两级 | `api.py` 应用层校验 | 🔴 |
| 2 | 同级目录名唯一 | `models.py` UNIQUE(parent_id, name) | 🔴 |
| 3 | 同目录用例名唯一 | `models.py` UNIQUE(directory, title) | 🔴 |
| 4 | 用例 ID 全局唯一 | `models.py` VARCHAR PK | 🔴 |
| 5 | 删除目录不影响用例 | FK SET_NULL | 🔴 |
| 6 | 删除非空目录拒绝 | `api.py` 有子目录或用例时拒绝 | 🔴 |
| 7 | el-cascader `emitPath: false` | `CaseEditor.vue` | 🔴 |
| 8 | 用例保存 `update_or_create` 全量覆盖 16 字段 | `views.py` | 🟠 |
| 9 | 未保存离开拦截（Dirty Tracking） | `CaseEditor.vue` `onBeforeRouteLeave` | 🟠 |
| 10 | 并发编辑 Last Write Wins | 无编辑锁 | 🟡 |
| 11 | 用例 title 必填 ≤500字符 | 前端校验 | 🟠 |
| 12 | 用例 package_name 必填 | 前端校验 | 🟠 |
| 13 | 单用例最大 100 步 | 前端校验 | 🟠 |
| 14 | 批量导入最大 500 条/次 | `views.py` | 🟠 |
| 15 | 目录树最大 10000 节点 | `api.py` | 🟡 |
| 16 | steps_json 最大 1MB | 后端校验 | 🟠 |

### 4.3 test-runner

| # | 约束 | 位置 | 严重 |
|:--:|------|:--:|:--:|
| 1 | 一台设备同时只执行一个任务 | `_device_busy` 集合 | 🔴 |
| 2 | 执行快照 selected_cases 在启动时保存 | `runner.py` | 🔴 |
| 3 | case FK SET_NULL 保护历史 | `models.py` | 🔴 |
| 4 | FIFO 出队在 finally 块触发 | `_start_next_queued()` | 🔴 |
| 5 | 排队取消后任务保留配置回到 idle | `cancel_queued_task` | 🟠 |
| 6 | 重新执行创建新卡片（新 ID + 第N轮后缀） | 前端逻辑 | 🟠 |
| 7 | 停止后关键状态为 done + outcome=stopped | WebSocket `run_finished` 处理 | 🟠 |
| 8 | 内存队列 `_device_queue` 服务器重启丢失 | 规划中修复 | 🟡 |

### 4.4 workflow

| # | 约束 | 位置 | 严重 |
|:--:|------|:--:|:--:|
| 1 | 不新增工作流专用后端端点 | 复用 device/runner/case API | 🔴 |
| 2 | 不新增第二套用例存储 | 运行链路复用 linkedCaseId → 用例库 | 🔴 |
| 3 | 从头运行前必须同步 + 无脏数据 | §2.2.4 | 🔴 |
| 4 | 从当前步运行 = 前端串行 run-step | MVP 技术约定 | 🟠 |
| 5 | 文档 doc_id 全局唯一 | `wf_documents` | 🔴 |
| 6 | 导入 doc_id 冲突 → 409 拒绝 | `views.py` | 🔴 |

### 4.5 AI Assistant

| # | 约束 | 位置 | 严重 |
|:--:|------|:--:|:--:|
| 1 | Tool 跨模块写必须走 `api.py` | `factory.py` → Tool | 🔴 |
| 2 | Tool 同进程调用，不走 HTTP | AgentScope Tool | 🟠 |
| 3 | Redis 不可用 → 降级 Django 阻塞模式 | 前端 `ChatView.vue` | 🟠 |
| 4 | API Key 加密存储 + 前端脱敏 | `encrypt_key()` / `mask_key()` | 🔴 |
| 5 | 智能体 20+ 配置参数全量保存 | `ai_agents` 表 | 🟠 |

---

## 五、三端对齐问题（已发现的不一致）

以下是在 PRD 演进中已暴露的"三端不同步"问题，AI 涉及相关改动时必须三端 grep 确认。

| # | 问题 | 前端 | 后端枚举/模型 | 执行引擎 | 以谁为准 |
|:--:|------|------|-------------|---------|---------|
| 1 | **步骤类型数量** | 编辑器 17 种 | `StepType` 枚举 17 种 | executor 支持 17 种（含 long_click/swipe/drag/wait_any） | 以 `executor.py` + `StepType` 为准 |
| 2 | **Tool 数量** | — | PRD 文档旧称 14，现网 ≈28 | `factory.py` 注册 ≈24 业务 + 4 Plan | 以 `factory.py` 为准 |
| 3 | **`wait_any` vs `wait_any`** | 前端用 `wait_any` | 部分代码有双名 | executor 两者都认 | grep 确认所有引用点 |
| 4 | **MD vs HTML 全功能规格** | — | — | — | 冲突时以 HTML + 现网代码为准（README 明确） |

---

## 六、错误处理模板（6 类 × 每个功能）

所有功能面对这 6 类异常时，必须按以下模式处理：

| 异常类别 | 前端行为 | 后端行为 | AI 编代码要求 |
|---------|---------|---------|-------------|
| **网络断连** | Toast 提示 + 保留编辑内容 + 读操作自动重试 / 写操作显示重试按钮 | 操作失败不写入 DB | catch 分支必须有 `ElMessage.error()`，禁止静默吞错 |
| **数据为空** | 空状态引导页（图标 + 文字 + CTA 按钮） | 返回空数组/空对象，不报错 | 每个列表/详情组件必须有空态，不能空白 |
| **权限不足** | JWT 401 → 自动刷新 → 失败跳 `/login` | 401 + `redirect` query | 不在组件内手写认证逻辑，走统一拦截器 |
| **重复提交** | 按钮 loading + disabled | 幂等（update_or_create / 去重） | 所有写操作按钮必须有 loading 态 |
| **输入非法** | 前端实时校验（blur + submit）+ 后端兜底 400 | 返回 400 + 具体字段错误 | 前端校验规则不能比后端宽松 |
| **超时** | 前端超时 + 错误提示，不伪造成功 | 操作超时返回 error | 不能写假成功回调掩盖超时 |

### 具体错误码映射

| 场景 | HTTP | `error` 文案模式 |
|------|:--:|------|
| 资源不存在 | 404 | `"{资源类型} {id} 未找到"` |
| 状态冲突 | 409 | 精确描述冲突（如 "设备已被 {user} 锁定"） |
| 参数校验失败 | 400 | 指出具体字段（如 "目录名称不能为空"） |
| 服务不可用 | 502/503 | 含恢复建议（如 "设备 ATX Agent 未运行，请在设备端启动 uiautomator2 服务"） |
| 内部错误 | 500 | 不暴露堆栈/路径/SQL |

---

## 七、Non-goals（禁止实现的功能）

以下功能在各 PRD 中明确标注为"本期不做"或"归属其他模块"。AI 不能自行实现。

| 功能 | 原因 | 归属 |
|------|------|------|
| 工作流：多设备并行调试 / 压力循环 / 截图流联播 | MVP 最小可用 | 工作流 v1.3+ |
| 工作流：完整日志 IDE / WS 全量日志 UI | 工作量大 | 工作流 v1.3+ |
| 工作流：新增后端端点 | 复用现有 API | 需改架构 |
| 工作流：原生 `start_step_index` | runner 不支持 | 需改 test-runner |
| 用例：三级及以上目录 | 两级已够用 | v4（暂不排期） |
| 用例：版本管理/回滚 | YAML 导出已覆盖 | v3 |
| 用例：BDD/Gherkin 语法 | 非核心 | v4（暂不排期） |
| 用例：评审/审批流 | 非测试工具核心 | v4（暂不排期） |
| 执行：队列状态持久化到 DB | 内存结构够用 | 规划中 |
| 执行：重启后排队恢复 | 同上 | 规划中 |
| 执行：WebSocket 断线自动重连 | 同上 | 规划中 |
| 设备：USB 转无线（adb tcpip） | 仅手动 IP 直连 | 后续迭代 |
| 设备：局域网自动发现（mDNS） | 手动输入 | 后续迭代 |
| 设备：iOS 设备管理 | 仅 Android | v4+ |
| 报告：Allure 集成 | 已替换为自建 HTML | — |
| 报告：邮件推送 | v3 通知系统 | project-hub |
| 仪表盘：写操作 | 纯聚合层 | 禁止 |

---

## 八、已知陷阱速查

| 陷阱 | 症状 | 根因 | 修复 |
|------|------|------|------|
| **el-cascader `emitPath`** | 保存成功但编辑回显不显示 | `emitPath` 默认 `true`，v-model 是路径数组而非叶子值 | 显式设 `:props="{ emitPath: false }"` |
| **animal-island-vue Button `type="danger"`** | 按钮不变红 | `danger` 是布尔属性不是 type 值 | `type="primary" danger` |
| **animal-island-vue Tabs 自闭合** | 内容渲染在组件外 | Tabs 内容必须用具名 slot | `<template #[tab.key]>` 放 Tabs 内部 |
| **Modal 内 Select** | 下拉被裁剪 | Modal `overflow:hidden` + `clip-path` | Modal 内用 `el-select`（Teleport 到 body） |
| **MsgPackSerializer** | WS HTTP 500 | `serializer_format='msgpack'` 不兼容 | 改为 `'json'` |
| **截图流空白** | 元素定位左侧空白 | WebSocket URL 直连后端端口而非走 Vite proxy | 用 `wsUrl('/ws/screenshot')` |
| **status vs running 双源** | 任务状态不一致 | 两个字段分别被不同代码路径更新 | 同时检查 `status` + `outcome` |
| **内存队列重启丢失** | 排队任务消失 | `_device_queue` 是内存 list | 当前无修复（规划中） |
| **wait_any / wait_any 双名** | 步骤类型识别失败 | 两套名字共存 | grep 确认所有引用 |

---

## 九、架构原则（从 PRD 提炼）

1. **读放开，写收敛**：跨模块 SELECT 可直接 ORM，INSERT/UPDATE/DELETE 必须走目标模块 `api.py`
2. **同进程调用**：AgentScope Tool → Django 直接 import，不走 HTTP
3. **设备操作同步阻塞**：uiautomator2 在 Daphne 工作线程执行，非 async
4. **SET_NULL 保护历史**：设备/目录/用例被删除时，关联的执行结果/用例/元素保留
5. **执行快照模式**：执行前复制完整用例数据到 `selected_cases`，确保历史可审计
6. **数据来源铁律**：前端数据只从 API 来，禁止 `ref([{...硬编码}])`
7. **写操作 catch 必须报错**：`ElMessage.error()`，禁止静默吞错
8. **JWT 统一认证**：Django + AgentScope 共享 `SECRET_KEY`
9. **不新增第二套存储**：工作流运行复用用例库，不走独立存储

---

## 十、模块 Review 清单（提交前自查）

> 来源：HTML 全功能规格 §治理与验收。每个模块 3 条核心检查项。

### 设备管理
| # | 检查项 | 通过标准 |
|:--:|------|------|
| D1 | 跨模块写只走 api | `acquire_device` / `release_device` 必须通过 `api.py` |
| D2 | 扫描幂等 | 同 serial 不产生重复行 |
| D3 | WIFI 校验 | 前端 IP/端口格式校验必做 |

### 元素定位
| # | 检查项 | 通过标准 |
|:--:|------|------|
| E1 | 改动范围 | 仅 `element_locator` + `modules/element-locator` |
| E2 | 防火墙 | 不写他模块表；设备写走 `device_pool.api` |
| E3 | WS 鉴权 | `/ws/screenshot` token 校验 |
| E4 | 无硬编码 | 元素列表数据来自 API |

### 用例管理
| # | 检查项 | 通过标准 |
|:--:|------|------|
| C1 | 唯一性 | ID 全局唯一；同目录 title UNIQUE |
| C2 | 步骤契约 | steps_json 与 executor 支持的步骤类型一致 |
| C3 | 无 TestCaseCache | 不写已删除的 `cm_test_cases` 表 |

### 执行引擎
| # | 检查项 | 通过标准 |
|:--:|------|------|
| T1 | 防火墙 | 无 `_active_runs` 穿透到其他模块 |
| T2 | 设备释放 | `finally` 块必须 release 设备 |
| T3 | 快照 | `selected_cases` 完整复制执行时步骤数据 |

### 测试报告
| # | 检查项 | 通过标准 |
|:--:|------|------|
| R1 | 数据源 | 列表基于 `tr_test_runs` + `tr_test_results` 聚合，非空文件 |
| R2 | 失败可追溯 | 失败用例 `detail` 字段非空 |
| R3 | 生成隔离 | 报告生成异常只打日志，不影响 runner 主流程 |

### AI 助手
| # | 检查项 | 通过标准 |
|:--:|------|------|
| A1 | Key 脱敏 | API 响应中 `api_key` 为 `sk-***xxxx` 格式 |
| A2 | 防火墙 | Tool 跨模块写走各模块 `api.py` |
| A3 | 无 DEPRECATED | 不用 `dashboard_views`，Tool 数量以 `factory.py` 为准 |

---

## 十一、文档真相来源

遇到不一致时，按以下优先级取信：

```
1. 现网代码（grep 确认）
2. 本手册
3. 子 PRD Markdown（可能过期，以末尾附录B「现状差距」为准）
4. 需求大纲.md
```
