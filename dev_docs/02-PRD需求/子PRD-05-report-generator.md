# 子PRD — 报告分析 (Report Generator)

> 关联模块：`apps/report_generator/` · 前端：`frontend/src/modules/report-generator/`
> 关联全局：`../全局PRD.md` · 关联执行：`./子PRD-04-test-runner.md`
> 版本：v3.0 · 状态：已实施 · 日期：2026-07-07

---

## 1. 模块功能目标

报告分析模块是测试平台的结果收口与质量可视化中枢，承担以下核心职责：

1. **在线报告查看**：每次执行完成后，生成结构化的在线 HTML 报告，用户可直接在平台内查看
2. **用例执行明细**：以表格形式展示每个用例的迭代结果，支持展开查看每次迭代详情
3. **失败分析定位**：自动聚合失败用例，展示失败迭代、失败原因、XPath 定位信息
4. **质量趋势可视化**：通过历史聚合统计，展示通过率趋势折线图 + 用例耗时柱状图
5. **报告导出**：支持 CSV/LOG 文件下载，用于离线分析或归档

### 1.1 用户交互流程

```
/reports (报告列表页)
  │ 表格展示所有执行任务
  │ 列：Run ID / 设备 / 用例数 / 通过 / 失败 / 通过率 / 状态 / 耗时 / 时间
  │
  ▼ 点击 Run ID 跳转
/reports/:runId (报告详情页)
  ├── KPI 摘要卡片（用例数 / 通过 / 失败 / 通过率）
  ├── Tab 1: 用例执行明细 — 表格 + 展开迭代详情
  ├── Tab 2: 失败分析 — 失败用例卡片 + 失败迭代详情
  └── Tab 3: 趋势图表 — 通过率趋势 + 耗时分布 + 历史记录表
```

### 1.2 数据来源

```
tr_test_runs (执行记录) + tr_test_results (迭代结果)
      │
      ▼ GET /api/reports/run/{run_id}
report-generator views.py
      │
      ├─ JOIN 查询 + 聚合计算
      └─ 返回结构化 JSON → 前端渲染
```

---

## 2. 功能清单与概述

| 编号 | 功能名称 | 优先级 | 一句话描述 |
|:--:|------|:--:|------|
| F-01 | 多格式报告生成 | P0 | 测试完成后自动生成 CSV/MD/LOG 文件，含失败详情 |
| F-02 | 报告列表与下载 | P0 | 执行任务表格列表，支持按状态筛选和文件下载 |
| F-03 | 在线报告详情页 | P0 | 点击 Run ID 进入完整报告：用例明细 + 失败分析 + 趋势图表 |
| F-04 | 趋势可视化 | P1 | Chart.js 渲染通过率趋势折线图 + 用例耗时柱状图 |

---

## 3. 功能详细规格

---

### 3.1 F-01：多格式报告生成

#### 3.1.1 需求定义

执行引擎每次完成测试后，自动调用 ReportGenerator 生成四种格式的测试报告：

| 格式 | 输出 | 内容 |
|------|------|------|
| CSV | `logs/result_{timestamp}.csv` | 用例名称 / 测试步骤 / 计划轮次 / 实际执行 / 通过 / 失败 / 成功率 |
| Markdown | `logs/result_{timestamp}_failures.md` | 失败详情：失败步骤 / 错误信息 / 日志片段 |
| Log | `logs/test_{timestamp}.log` | 完整运行日志（所有步骤 + 执行时间） |
| JSON | `exports/report_{timestamp}.json` | 结构化报告（所有字段的 JSON 表示） |

#### 3.1.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 报告生成覆盖率 | 每次执行完成 → 自动生成 CSV + LOG | 100% |
| 失败详情完整性 | 每次 fail 有对应的失败原因记录 | 100% |
| 报告可读性 | 非技术人员可直接打开 CSV 看懂结果 | — |

#### 3.1.3 触发条件

- TestRunner.run() 执行完成 → 自动调用 `ReportGenerator.save_csv(results, failure_details)` + `ReportGenerator.save_log(run_id, log_lines)`
- 无手动触发入口

#### 3.1.4 业务规则

**CSV 生成**（`save_csv`）：

```
CSV 表头：
用例名称, 测试步骤, 计划轮次, 实际执行, 通过, 失败, 成功率

示例行：
login_test, "点击登录→等待首页", 3, 3, 3, 0, 100.00%
order_test, "点击下单→验证金额", 3, 3, 2, 1, 66.67%
```

**失败详情 MD**（`_save_failure_md`）：

```markdown
## 失败详情

### login_test (迭代 3) — FAIL

- 步骤 index: 2
- 步骤类型: verify_text
- XPath: //*[@text='订单已创建']
- 期望文本: 订单已创建
- 实际文本: 网络连接超时
- 耗时: 12.3s

### order_test (迭代 1) — FAIL

- ...
```

**日志文件**（`save_log`）：

```
[2026-06-30 15:30:01] === 测试运行开始 ===
[2026-06-30 15:30:01] 用例: login_test - 登录流程测试
[2026-06-30 15:30:02] [迭代 1] 开始
[2026-06-30 15:30:03] [PASS] click: 点击登录按钮 (0.8s)
[2026-06-30 15:30:05] [PASS] wait: 等待首页出现 (2.1s)
[2026-06-30 15:30:05] [迭代 1] PASS (3.2s)
...
[2026-06-30 15:30:10] === 测试运行完成 | 通过: 6, 失败: 0, 总耗时: 45.2s ===
```

**JSON 报告**（`generate_json_report`）：

```json
{
  "run_id": "20260630_153000",
  "generated_at": "2026-06-30T15:30:10+08:00",
  "summary": {"total_pass": 6, "total_fail": 0, "total_duration": 45.2},
  "cases": [
    {
      "case_id": "login_test",
      "title": "登录流程测试",
      "iterations": [
        {"iteration": 1, "result": "pass", "duration_ms": 3200},
        {"iteration": 2, "result": "pass", "duration_ms": 3100}
      ],
      "pass": 3, "fail": 0, "rate": "100%"
    }
  ],
  "failures": []
}
```

#### 3.1.5 前端交互要求

报告生成无前端直接交互，由后端自动完成。

#### 3.1.6 后端核心组件

| 方法 | 功能 |
|------|------|
| `ReportGenerator.save_csv(results, failure_details)` | 生成 CSV + 失败详情 MD |
| `ReportGenerator.save_log(run_id, log_lines)` | 保存运行日志 |
| `ReportGenerator.generate_json_report(results, failure_details)` | 生成 JSON 报告 |
| `ReportGenerator.save_json_report(results, failure_details)` | 落盘 JSON 报告 |

---

### 3.2 F-02：报告列表与下载

#### 3.2.1 需求定义

用户进入报告模块后看到执行任务表格，每行对应一次测试执行，点击 Run ID 进入详情页。同时保留 CSV/LOG 文件下载能力。

#### 3.2.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 报告可见性 | 每次执行后记录出现在列表 | 100% |
| 下载可用性 | 点击下载 → 浏览器下载文件 | 100% |

#### 3.2.3 触发条件

- 用户进入 report-generator 页面 → 自动加载执行记录列表
- 用户点击 Run ID → 跳转到 `/reports/:runId`

#### 3.2.4 业务规则

```
报告列表查询（从 DB 实时查询）：
1. 查询 tr_test_runs 表，按 id 倒序
2. annotate 聚合 tr_test_results：total（迭代总数）/ passed（通过数）
3. 从 selected_cases 快照获取 case_count
4. 计算 failed = total - passed, rate = passed/total × 100%
5. 计算 duration = finished_at - started_at
6. 返回：run_id / status / device_serial / loop_count / case_count / total / passed / failed / rate / duration / started_at / finished_at
```

#### 3.2.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| 报告列表 | 执行任务表格，列：Run ID(可点击) / 设备 / 用例数 / 通过(绿) / 失败(红) / 通过率(进度条) / 状态(徽章) / 耗时 / 时间 |
| 状态筛选 | Tabs：全部 / 已完成 / 失败 / 已停止 |
| 空状态 | 无记录时显示「暂无执行记录，请先执行测试」 |

---

### 3.3 F-03：在线报告详情页

#### 3.3.1 需求定义

用户从报告列表点击 Run ID，进入该次执行的完整报告页面。报告包含三个页签：

| 页签 | 内容 |
|------|------|
| 用例执行明细 | KPI 摘要卡片 + 用例结果表格（用例ID/名称/计划/实际/通过/失败/成功率/状态），点击展开查看每次迭代详情 |
| 失败分析 | 仅失败时出现，展示每个失败用例的失败迭代、失败原因 |
| 趋势图表 | Chart.js 通过率趋势折线图 + 用例平均耗时柱状图 + 近期执行记录表 |

#### 3.3.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 报告可见性 | 每次执行后点击 Run ID 可查看 | 100% |
| 失败可定位性 | 失败用例能追溯到具体迭代和原因 | 100% |
| 图表可交互性 | 鼠标悬停显示具体数值 | ✅ |

#### 3.3.3 业务规则

```
报告详情查询：
1. 根据 run_id 查询 tr_test_runs 获取运行元数据
2. 查询 tr_test_results WHERE run_id = ? 获取所有迭代结果
3. 按 case_id 分组聚合：每用例 pass/fail/rate
4. 计算整体 pass_rate = total_pass / total_iterations × 100%
5. 查询最近 10 条 runs 计算通过率趋势
6. 数据全部来自 DB 实时查询，不依赖预生成的文件
```

#### 3.3.4 前端交互要求

| 变动项 | 描述 |
|--------|------|
| 报告列表 | 执行任务表格，点击 Run ID 跳转到 `/reports/:runId` |
| 详情页头 | 返回按钮 + 运行元数据（设备/轮次/耗时/状态） |
| KPI 卡片 | 4 列：用例数 / 通过(绿) / 失败(红) / 通过率(颜色随值变化) |
| 用例表格 | 支持行展开查看迭代详情，失败行红色高亮 |
| 失败分析 | 失败用例用 red pattern Card 展示，内含迭代失败表 |
| 趋势图表 | Chart.js 折线图 + 横柱图，卡片容器 |

#### 3.3.5 后端接口

| 接口 | 核心行为 |
|------|---------|
| `GET /api/reports/run/{run_id}` | 聚合查询 + 返回结构化报告 JSON。详见附录 §4.3.3 |

---

### 3.4 F-04：趋势可视化

#### 3.4.1 需求定义

在报告详情页的趋势页签中，使用 Chart.js 渲染两个图表 + 一个历史记录表：

| 图表 | 数据来源 | 说明 |
|------|---------|------|
| 通过率趋势折线图 | recent_runs（近 10 次执行） | 横轴时间，纵轴通过率%，支持 hover 显示具体值 |
| 用例耗时柱状图 | 本次执行的 cases | 横向柱状图，失败用例红色标注 |
| 近期执行记录表 | recent_runs | 每次执行的 Run ID / 总数 / 通过 / 失败 / 通过率 / 时间 |

#### 3.4.2 业务规则

```
Chart.js 集成：
1. 通过 CDN script 标签加载 chart.js@4.4.7 UMD 版本
2. 组件内通过 window.Chart 引用
3. watch activeTab → 切换到 trend 时延迟 100ms 渲染（确保 canvas 已挂载）
4. onUnmounted 时 destroy 图表实例防止内存泄漏
```

---

## 4. 附录

### 4.1 数据模型

#### 4.1.1 rg_reports（报告记录）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BigAutoField | PK | 自增主键 |
| `run_id` | CharField(200) | INDEX | 关联执行 run_id |
| `title` | CharField(500) | — | 报告标题 |
| `file_type` | CharField(20) | default='csv' | 文件类型 (csv/md/log/json) |
| `file_path` | CharField(1000) | — | 文件路径 |
| `created_at` | DateTimeField | auto_now_add | 创建时间 |

#### 4.1.2 rg_report_templates（报告模板，v3 预留）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BigAutoField | PK | 自增主键 |
| `name` | CharField(200) | — | 模板名称 |
| `config` | JSONField | default=dict | 模板配置 |
| `created_at` | DateTimeField | auto_now_add | 创建时间 |

---

### 4.2 API 接口规格

| # | 方法 | 路径 | 功能 |
|---|------|------|------|
| 1 | GET | `/api/reports` | 执行记录列表（查询 tr_test_runs） |
| 2 | GET | `/api/reports/run/{run_id}` | 单次执行完整报告（聚合查询） |
| 3 | GET | `/api/reports/{filename}` | 下载报告文件 |
| 4 | GET | `/api/reports/{filename}/content` | 在线查看文件内容 |

**GET /api/reports**

Response 200:
```json
{
  "ok": true,
  "runs": [
    {
      "run_id": "run_RF8N21MSW7A_20260707_143025",
      "status": "COMPLETED",
      "device_serial": "RF8N21MSW7A",
      "loop_count": 3,
      "case_count": 8,
      "total": 24, "passed": 22, "failed": 2,
      "rate": 92, "duration": "1m53s",
      "started_at": "2026-07-07T14:30:25",
      "finished_at": "2026-07-07T14:32:18"
    }
  ]
}
```

**GET /api/reports/run/{run_id}**

Response 200:
```json
{
  "ok": true,
  "run": {
    "run_id": "...",
    "status": "COMPLETED",
    "device_serial": "...",
    "loop_count": 3,
    "started_at": "...",
    "finished_at": "...",
    "duration": "1m53s",
    "total_iterations": 24, "total_pass": 22, "total_fail": 2,
    "pass_rate": 91.7, "case_count": 8,
    "cases": [
      {
        "case_id": "login_test",
        "case_title": "登录流程测试",
        "planned": 3, "actual": 3, "pass": 3, "fail": 0, "rate": 100,
        "iterations": [
          {"iteration": 1, "result": "pass", "duration_ms": 3200, "detail": ""}
        ]
      }
    ],
    "recent_runs": [
      {"run_id": "...", "started_at": "...", "total": 24, "passed": 22, "failed": 2, "rate": 92}
    ]
  }
}
```

---

### 4.3 非功能需求

| 类别 | 指标 | 目标值 |
|------|------|:--:|
| **性能** | 报告生成耗时 | 执行完成后 ≤500ms |
| **性能** | 报告列表查询 | ≤300ms |
| **可靠性** | 报告生成失败不影响测试记录 | 失败时记录 error 日志，test-runner 正常完成 |

---

### 4.6 非目标（Non-goals）

| 功能 | 原因 | 归属 |
|------|------|------|
| Allure 报告集成 | 已替换为自建 HTML 在线报告，更可控无外部依赖 | — |
| 报告邮件推送 | v3 通知系统 | project-hub |
| 报告在线编辑/批注 | 非测试工具核心 | v4 |
| 报告对比/差异分析 | v3 | v3 |
| 多团队报告隔离 | 依赖 project-hub | project-hub v3 |

---

### 4.5 里程碑

| 阶段 | 交付物 | 对应功能 |
|------|------|----------|
| v1 ✅ | CSV/MD/LOG 生成 + 报告列表下载 | F-01, F-02 |
| v2 ✅ | 在线报告详情页 + 趋势图表 | F-03, F-04 |
| v3 | 趋势对比 + 邮件推送 + 报告导出 PDF | — |

---

## 变更记录

| 版本 | 日期 | 变更类型 | 变更摘要 |
|------|------|----------|----------|
| v1.0 | 2026-06-30 | — | v1 实现完成：CSV/MD/LOG 生成 + 列表下载 |
| v2.0 | 2026-06-30 | 重写 | 统一 6 维度结构，补充 Allure 规划和执行历史方案 |
| v3.0 | 2026-07-07 | 重设计 | 报告模块重设计：两级页面结构（列表→详情），三页签（用例明细/失败分析/趋势图表），DB 驱动 API，Chart.js 可视化，Allure 方案替换为自建 HTML 报告 |
