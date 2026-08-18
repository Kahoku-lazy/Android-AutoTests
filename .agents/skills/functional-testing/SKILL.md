---
name: functional-testing
description: |
  功能测试 — 代码变更后从功能/接口/安全/数据表单/性能五个维度评估，执行测试，发现 Bug 并输出报告。
  Keywords: 测试一下, 验证功能, 验收, 功能测试, 跑一下测试, 回归测试, 检查功能, verify
  Trigger: 用户表达"测试/验证/验收/检查"某个功能或代码变更时。
---

# Functional Testing

**目的**: 发现代码审查无法看到的问题 — 运行时 Bug、设计缺陷、安全漏洞、性能瓶颈。

**能力模型**: 规划(Plan) → 执行(Execute) → 审核(Review) → 验证(Verify)

## 五维测试模型

每次测试从五个维度评估，每个场景至少覆盖 3 个维度：

| 维度 | 代号 | 测什么 | 发现什么 |
|------|:--:|------|------|
| **功能** | FUNC | 数据一致性 + 行为正确性 | 数据不同步、操作无效、状态错误 |
| **接口** | API | 请求校验 + 响应格式 + HTTP 状态码 | 缺校验、500 崩溃、响应格式不一致 |
| **安全** | SEC | 认证 + 授权 + 加密 + 防注入 | 未认证可访问、数据泄露、明文存储 |
| **数据表单** | DATA | 字段约束 + 类型校验 + 默认值 | 必填为空不报错、类型错误崩溃 |
| **性能** | PERF | 响应时间 + 稳定性 + 并发 | 慢查询、超时、脏写 |

> 详细判断标准见 `references/test-case-design.md`。

## 工作流

### Phase 1: Plan（规划）

```
1. 识别改动 → git diff --name-only
2. 映射模块 → tests/functional/{module}/
3. 判断维度 → 根据变更类型确定最少覆盖维度:
   - 新增 API → FUNC + API + SEC (最少 5 条)
   - 修改逻辑 → API + SEC + DATA (最少 4 条)
   - 新增页面 → FUNC + PERF (最少 3 条)
   - Bug 修复 → FUNC + SEC (最少 2 条，含复现)
4. 加载 test_spec.md → 匹配已有用例
5. 无覆盖 → 按 test-case-design.md 规范新建
```

### Phase 2: Execute（执行）

```bash
python tests/functional/{module}/run_tests.py              # 全量
python tests/functional/{module}/run_tests.py --dim FUNC   # 单维度
python tests/functional/{module}/run_tests.py --case ID    # 单条
```

### Phase 3: Review（审核）

检查测试结果，识别两类 Bug：

| Bug 类型 | 判断 | 示例 |
|---------|------|------|
| **代码 Bug** | 实现与预期不符 | catch 静默吞错、数据未同步、500 崩溃 |
| **设计 Bug** | 功能设计本身有缺陷 | 缺认证、无输入校验、无并发保护 |

输出报告（维度覆盖表 + Bug 清单 + 结论）。

### Phase 4: Verify（验证）

```
1. 修复后重新执行失败用例
2. 回归关联功能（同一模块的其他用例）
3. 清理测试数据（先验证非生产数据）
4. 最终确认: 全部 PASS + 数据库干净
```

## 清理测试数据

```
验证三步:
  [ ] name 以 "TEST-" 开头
  [ ] created_at 在 10 分钟内
  [ ] 数量 = 测试创建的数量
  → 全部满足 → 安全删除（需用户确认）
  → 任一项不满足 → 中止，人工确认
```

## 关联文件

| 文件 | 何时加载 |
|------|---------|
| `references/test-case-design.md` | 新建用例时加载 |
| `tests/functional/{module}/test_spec.md` | 匹配到模块时加载 |
| `tests/functional/{module}/run_tests.py` | 执行时调用 |
| `scripts/report_generator.py` | 生成 HTML 报告时调用 |
| `html-report` skill | 生成 HTML 报告时加载 design token |

## HTML 报告

测试执行后自动生成 HTML 报告，输出到 `tests/functional/{module}/reports/`:

- `report_{timestamp}.html` — 带时间戳的完整报告
- `report_latest.html` — 始终指向最新报告

### 自定义语言

```python
# 默认中文
generate_report("Dashboard", results)

# 英文
generate_report("Dashboard", results, lang="en")

# 添加新语言：编辑 scripts/report_generator.py 的 _labels() 函数
```

### 报告内容

执行摘要 → KPI 卡片 → 逐用例详情 → 维度热力图 → Bug 证据清单 → 测试方向建议。
样式与 Doodle Craft 主题一致: Nunito 字体、不对称圆角、暖木色配色、粗线卡片。
