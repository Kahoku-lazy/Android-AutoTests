# 子PRD — 报告分析 (Report Generator)

> 关联模块：`apps/report_generator/` · 前端：`frontend/src/modules/report-generator/`
> 关联全局：`../全局PRD.md` · 关联执行：`../子PRD/04-test-runner.md`
> 版本：v2.0 · 状态：草稿 · 日期：2026-06-30

---

## 1. 模块功能目标

报告分析模块是测试平台的结果收口与质量可视化中枢，承担以下核心职责：

1. **测试报告生成**：在执行引擎完成测试后，自动生成 CSV 结果文件 + 失败详情 Markdown + 运行日志文件 + JSON 结构化报告
2. **报告查阅与下载**：提供报告文件列表浏览和下载能力，支持历史执行记录聚合统计
3. **失败原因追溯**：失败详情包含失败步骤、错误信息、执行日志片段，帮助用户快速定位问题
4. **质量趋势可视化**（v2）：通过执行历史聚合统计，展示通过率趋势、失败 Top N 用例、耗时分布

### 1.1 模块边界

```
test-runner (执行引擎)
      │
      ▼ 每次执行完成 → TestRunner.run() 调用 ReportGenerator
report-generator
      │
      ├─ save_csv(case_results, failure_details) → logs/result_{ts}.csv + _failures.md
      ├─ save_log(run_id, log_lines)             → logs/test_{ts}.log
      └─ generate_json_report(results, failures)  → dict (可选落盘)
```

---

## 2. 功能清单与概述

| 编号 | 功能名称 | 优先级 | 一句话描述 |
|:--:|------|:--:|------|
| F-01 | 多格式报告生成 | P0 | 测试完成后自动生成 CSV/MD/LOG/JSON 四种格式报告，含失败详情 |
| F-02 | 报告列表与下载 | P0 | 列出 logs/ 下所有报告文件，支持按时间排序和下载 |
| F-03 | 执行历史聚合 | P1 | 聚合展示历次执行的总数/通过/失败/通过率，支持按时间排序 |
| F-04 | Allure 报告（v2 规划）| P1 | 生成 Allure 兼容的 JSON 数据 + 前端集成 Allure Report 展示 |

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

用户可以在平台上浏览所有历史报告文件（CSV/MD/LOG），按修改时间倒序排列，点击下载。

#### 3.2.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 报告可见性 | 每次执行后报告出现在列表 | 100% |
| 下载可用性 | 点击下载 → 浏览器下载文件 | 100% |

#### 3.2.3 触发条件

- 用户进入 report-generator 页面 → 自动加载报告列表
- 用户点击报告行"下载"

#### 3.2.4 业务规则

```
报告列表查询：
1. 扫描 logs/ 目录下所有文件
2. 过滤：result_* 和 test_* 前缀的文件
3. 提取文件类型（csv/md/log）
4. 按修改时间倒序排列
5. 返回：文件名 / 类型 / 大小 / 修改时间
```

**下载**：`GET /api/reports/{filename}` → 根据文件扩展名设置 Content-Type（text/csv / text/markdown / text/plain），返回文件流。

#### 3.2.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| 报告列表 | el-table 列：文件名 / 类型（图标）/ 大小 / 时间 / 下载 |
| 下载按钮 | 直接 `<a :href="'/api/reports/' + filename" download>` |
| 空状态 | 无报告时显示「暂无报告，请先执行测试」 |

#### 3.2.6 后端接口要求

| 接口 | 核心行为 |
|------|---------|
| `GET /api/reports` | 列出 logs/ 下报告文件。详见附录 §4.3.1 |
| `GET /api/reports/{filename}` | 下载指定文件。详见附录 §4.3.2 |

---

### 3.3 F-03：执行历史聚合

#### 3.3.1 需求定义

聚合展示历次测试执行的统计数据（总数/通过/失败/通过率/耗时），帮助用户快速了解整体质量趋势。

#### 3.3.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 历史数据完整性 | 每次执行后可从历史中查到 | 100% |
| 历史查询性能 | 100 条历史记录响应 | ≤500ms |

#### 3.3.3 触发条件

- 用户进入 report-generator 页面
- 同时加载报告文件列表和执行历史

#### 3.3.4 业务规则

```
执行历史聚合：
1. 查询 tr_test_runs WHERE status='COMPLETED'
2. 对每条 run：
   - 提取 summary JSON 中的 total_pass / total_fail
   - 计算通过率 = total_pass / (total_pass + total_fail) × 100%
   - 计算执行时长 = finished_at - started_at
3. 按 started_at 倒序排列
4. 返回：run_id / device_serial / 通过/失败/通过率/耗时/时间
```

#### 3.3.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| 双栏布局 | 左栏：报告文件列表；右栏：执行历史表 |
| 历史表列 | run_id / 设备 / 通过数(绿) / 失败数(红) / 通过率(进度条) / 耗时 / 时间 |
| 通过率进度条 | el-progress：绿 ≥95% / 黄 ≥80% / 红 <80% |

#### 3.3.6 后端接口要求

| 接口 | 核心行为 |
|------|---------|
| `GET /api/runner/runs` | 返回执行历史（由 test-runner 提供）。详见 test-runner PRD §4.3.4 |

---

### 3.4 F-04：Allure 报告（v2 规划）

#### 3.4.1 需求定义

生成兼容 Allure Framework 的测试报告数据，前端集成 Allure Report 静态页面展示，提供步骤级失败截图、耗时分布、历史趋势的可视化呈现。

#### 3.4.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| Allure 数据生成 | allure-python 标准 JSON 输出 | 100% 兼容 |
| Allure Report 展示 | 前端可嵌入 Allure 静态报告页面 | — |

#### 3.4.3 业务规则 (v2 规划)

```
Allure 集成方案：
1. allure-python → 生成 allure-results/ 目录（suite/case/step JSON）
2. allure generate → 生成 allure-report/ 静态 HTML
3. 方案 A：django 静态文件目录，嵌入前端 iframe
4. 方案 B：独立 nginx 服务，前端跳转
5. 优先方案 A（简单，无额外服务依赖）
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
| 1 | GET | `/api/reports` | 报告文件列表 |
| 2 | GET | `/api/reports/{filename}` | 下载报告文件 |

**GET /api/reports**

Response 200:
```json
{
  "ok": true,
  "reports": [
    {
      "name": "result_20260630_153000.csv",
      "type": "csv",
      "size": 2048,
      "modified": "2026-06-30T15:30:10+08:00"
    },
    {
      "name": "result_20260630_153000_failures.md",
      "type": "md",
      "size": 1024,
      "modified": "2026-06-30T15:30:10+08:00"
    }
  ]
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

### 4.4 非目标（Non-goals）

| 功能 | 原因 | 归属 |
|------|------|------|
| 报告邮件推送 | v3 通知系统 | project-hub |
| 报告在线编辑/批注 | 非测试工具核心 | v4 |
| 报告对比/差异分析 | v3 | v3 |
| 多团队报告隔离 | 依赖 project-hub | project-hub v3 |
| 报告导出 PDF/PPT | 当前 CSV + JSON 已够用 | v4 |

---

### 4.5 里程碑

| 阶段 | 交付物 | 对应功能 |
|------|------|----------|
| v1 ✅ | CSV/MD/LOG/JSON 生成 + 报告列表下载 | F-01, F-02 |
| v2 当前 | 执行历史聚合 + Allure 报告 | F-03, F-04 |
| v3 | 趋势图表 + 邮件推送 + 报告对比 | — |

---

## 变更记录

| 版本 | 日期 | 变更类型 | 变更摘要 |
|------|------|----------|----------|
| v1.0 | 2026-06-30 | — | v1 实现完成：CSV/MD/LOG 生成 + 列表下载 |
| v2.0 | 2026-06-30 | 重写 | 统一 6 维度结构，补充 Allure 规划和执行历史方案 |
