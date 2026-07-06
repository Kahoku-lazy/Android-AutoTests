# Case-Manager 全功能自动化测试用例

**模块**: case-manager | **页面**: /cases | **测试框架**: Django ORM + requests + Playwright

---

## 用例清单

| 编号 | 层 | 描述 |
|------|:--:|------|
| CASE-DB-01 | DB | 用例物理删除后数据库中不存在 (TestDefinition.objects.filter) |
| CASE-DB-02 | DB | 删除目录后用例 directory_id 置 NULL (SET_NULL) |
| CASE-DB-03 | DB | IoT 字段默认值 (priority=P1, design_method='', precondition='') |
| CASE-DB-04 | DB | steps_json 字段正确存储 (JSON 序列化/反序列化) |
| CASE-DB-05 | DB | 新建用例默认 enabled=True |
| CASE-DB-06 | DB | YAML 导出后 TestCaseCache 表有记录 |
| CASE-DB-07 | DB | TC-ID 格式 TC-YYYYMMDD-HHMMSS-XXXX |
| CASE-DB-08 | DB | 同级目录名唯一约束生效 (UNIQUE(parent, name)) |
| CASE-API-03 | API | POST 创建 → GET 回读所有字段一致 (往返验证) |
| CASE-API-04 | API | POST 更新 title/priority → GET 验证字段已变更 |
| CASE-API-05 | API | DELETE 不存在的用例返回 ok=True (幂等) |
| CASE-API-06 | API | GET /definitions 返回 definitions 数组 |
| CASE-API-07 | API | 批量导入 3 条用例 → imported=3 |
| CASE-API-08 | API | 批量移动用例到目标目录 → moved=1 |
| CASE-API-09 | API | 删除非空目录返回 409 |
| CASE-API-10 | API | 创建三级目录被拒绝 (超过两级限制) |
| CASE-FUNC-01 | UI | 页面正常加载，左侧目录树 + 右侧内容区 + 工具栏均可见 |
| CASE-FUNC-02 | UI | 目录树显示已有目录结构 |
| CASE-FUNC-03 | UI | 卡片视图默认显示用例卡片 |
| CASE-FUNC-04 | UI | 切换到列表视图，显示表格 |
| CASE-FUNC-05 | UI | 切换回卡片视图 |
| CASE-FUNC-06 | UI | 点击目录树节点，用例列表按目录过滤 |
| CASE-FUNC-07 | UI | 点击面包屑「全部用例」恢复全部显示 |
| CASE-FUNC-08 | UI | 新建用例按钮跳转到编辑页 /cases/new |
| CASE-FUNC-09 | UI | 用例编辑页完整加载（基本信息表单 + 步骤编排区域） |
| CASE-FUNC-10 | UI | 新建用例自动生成 TC-ID 格式 |
| CASE-FUNC-15 | UI | 添加步骤后步骤列表增加一项 |
| CASE-FUNC-19 | UI | 展开步骤显示类型选择器 |
| CASE-FUNC-22 | UI | 点击用例卡片显示详情面板 |
| CASE-FUNC-29 | UI | 右键目录 → 新建用例跳转编辑页 |
| CASE-FUNC-33 | UI | 批量选择模式显示复选框 |
| CASE-FUNC-18 | UI | 空目录或有数据正确渲染 |
| CASE-API-01 | API | 通过 API 创建目录，页面刷新后可见 |
| CASE-API-02 | API | 通过 API 删除目录，页面刷新后消失 |
| CASE-DATA-01 | DATA | 用例卡片正常渲染 |
| CASE-DATA-02 | DATA | 目录树节点或空状态显示 |
| CASE-WHITE-01 | WHITE | 前端源码无硬编码密码 (admin123/autotests2026) |
| CASE-WHITE-02 | WHITE | 写操作 catch 包含错误处理 (ElMessage.error/formatApiError) |
| CASE-WHITE-03 | WHITE | 用例 API 响应不包含 api_key 字段 |
| CASE-WHITE-04 | WHITE | 前端 ref 初始值无硬编码假数据 ref([{...}]) |

---

## 层次分布

| 层次 | 技术 | 用例数 |
|------|------|:--:|
| DB | Django ORM 直连 | 8 |
| API | requests HTTP | 10 |
| UI | Playwright | 20 |
| WHITE | 源码静态分析 | 4 |
| DATA | 数据验证 | 2 |
| **总计** | | **44** |

---

## 运行方式

```bash
# 全量
python tests/functional/case-manager/run_tests.py

# 按层次
python tests/functional/case-manager/run_tests.py --layer DB
python tests/functional/case-manager/run_tests.py --layer API
python tests/functional/case-manager/run_tests.py --layer UI
python tests/functional/case-manager/run_tests.py --layer WHITE

# 单条
python tests/functional/case-manager/run_tests.py --case CASE-DB-01

# HTML 报告
open tests/functional/case-manager/reports/report_latest.html
```

## 依赖

- Django :8765 (DB + API 层)
- Vite :5173 (UI 层, 需 Playwright)
- Playwright: `pip install playwright && playwright install chromium`
