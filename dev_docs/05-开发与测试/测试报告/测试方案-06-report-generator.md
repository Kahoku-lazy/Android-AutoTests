# 模块测试方案 — 报告分析

> 关联子PRD：`02-PRD需求/子PRD-05-report-generator.md` · 版本：v1.0 · 日期：2026-06-30

---

## 1. 测试范围

| 类型 | 内容 |
|------|------|
| 格式测试 | CSV / Markdown / JSON 三种格式正确性 |
| 内容测试 | 通过率、失败截图、执行时间统计 |
| 编码测试 | 中文 UTF-8-BOM 兼容 |

---

## 2. CSV 报告测试

| 编号 | 用例 | 预期 |
|:--:|------|------|
| RG-CSV-01 | 基础 CSV | 含列：case_name/step_type/status/duration/timestamp |
| RG-CSV-02 | 中文内容 | 用例名含中文 → 用 Excel 打开不乱码 |
| RG-CSV-03 | 全部 PASS | pass_rate=100%，fail_count=0 |
| RG-CSV-04 | 含失败 | fail_count>0，失败行标注 |

---

## 3. Markdown 报告测试

| 编号 | 用例 | 预期 |
|:--:|------|------|
| RG-MD-01 | 基础 MD | 标题 + 统计表 + 失败详情 |
| RG-MD-02 | 失败详情 | 含：步骤编号 / 步骤类型 / XPath / 错误信息 |
| RG-MD-03 | 无失败时 | 不生成 failures.md 或标注"全部通过" |

---

## 4. JSON 报告测试

| 编号 | 用例 | 预期 |
|:--:|------|------|
| RG-JSON-01 | 基础结构 | 含 run_id/total/passed/failed/steps[] |
| RG-JSON-02 | 步骤详情 | 每条步骤含 type/xpath/status/duration/screenshot |
| RG-JSON-03 | 合法 JSON | JSON.parse 不报错 |

---

## 5. Allure 报告测试（v2）

| 编号 | 用例 | 预期 |
|:--:|------|------|
| RG-ALLURE-01 | 生成 Allure 目录 | 执行后生成 allure-results/ |
| RG-ALLURE-02 | 报告可打开 | allure open → 浏览器展示 |
| RG-ALLURE-03 | 趋势图 | 多次执行后趋势线显示 |
| RG-ALLURE-04 | 失败截图 | 失败步骤含截图附件 |

---

## 6. 边界测试

| 编号 | 用例 | 场景 | 预期 |
|:--:|------|------|------|
| RG-EDGE-01 | 无执行记录时请求报告 | 空数据库 | 返回空列表，不崩溃 |
| RG-EDGE-02 | 超大报告 (10000 步骤) | 压力测试后生成 | 不超时，文件可打开 |

---

## 变更记录

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.0 | 2026-06-30 | 基于子PRD v1.0 输出，v1 覆盖 CSV/MD/JSON，v2 升级 Allure |
