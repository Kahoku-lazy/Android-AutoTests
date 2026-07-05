# 模块测试方案 — 用例工程

> 关联子PRD：`02-PRD需求/子PRD/03-case-manager.md` · 版本：v1.0 · 日期：2026-06-30

---

## 1. 测试范围

| 类型 | 内容 |
|------|------|
| 接口测试 | 9 个 REST API |
| 前端测试 | 用例列表、拖拽排序、步骤编排 |
| 数据测试 | YAML 导入导出 |

---

## 2. 用例 CRUD 测试

| 编号 | 用例 | 预期 |
|:--:|------|------|
| CM-API-01 | 创建用例 (含 14 种步骤) | 201，返回 case_id |
| CM-API-02 | 创建用例 (空步骤) | 201，steps=[] |
| CM-API-03 | 创建用例 (缺包名) | 400，提示 package_name required |
| CM-API-04 | 获取用例列表 | 200，支持 ?project_id 过滤 |
| CM-API-05 | 获取单个用例 | 200，含完整 steps JSON |
| CM-API-06 | 更新用例 (修改名称/包名/步骤) | 200 |
| CM-API-07 | 更新步骤顺序 (拖拽) | 200，order 数组已更新 |
| CM-API-08 | 删除用例 | 200，级联删除关联结果 |
| CM-API-09 | 删除不存在的用例 | 404 |
| CM-API-10 | 启用/停用用例 | 200，enabled 切换 |

---

## 3. 14 种步骤类型验证

| 编号 | 步骤类型 | 测试验证点 |
|:--:|------|------|
| CM-ST-01 | `start_app` | 指定包名 → app 启动 |
| CM-ST-02 | `kill_app` | 指定包名 → app 强制停止 |
| CM-ST-03 | `restart_app` | kill + start 组合 |
| CM-ST-04 | `click` | XPath → 点击，元素存在则成功 |
| CM-ST-05 | `click_indexed` | XPath + index → 多个匹配时点第 N 个 |
| CM-ST-06 | `retry_click` | XPath → 失败后自动重试 (默认 3 次) |
| CM-ST-07 | `wait` | XPath → 轮询等待元素出现，支持 timeout |
| CM-ST-08 | `wait_disappear` | XPath → 等待元素消失 |
| CM-ST-09 | `wait_either` | 两个 XPath → 任一出现即继续 |
| CM-ST-10 | `wait_toast` | text → 等待 Toast 提示出现 |
| CM-ST-11 | `verify_text` | XPath + expected → 验证文本 |
| CM-ST-12 | `poll_text` | XPath → 轮询读取文本直到变化 |
| CM-ST-13 | `sleep` | seconds → 线程休眠 |
| CM-ST-14 | `log` | message → 写入执行日志 |

---

## 4. YAML 导入导出

| 编号 | 用例 | 预期 |
|:--:|------|------|
| CM-YAML-01 | 导出 YAML | 200，YAML 格式正确，含所有步骤 |
| CM-YAML-02 | 导入 YAML | 201，用例创建，步骤完整 |
| CM-YAML-03 | 导入格式错误 YAML | 400，提示解析错误 |
| CM-YAML-04 | 导入不支持的步骤类型 | 400，提示 unknown type |
| CM-YAML-05 | 导出再导入一致性 | 内容一致，不丢字段 |

---

## 5. 前端测试

| 编号 | 用例 | 预期 |
|:--:|------|------|
| CM-UI-01 | 用例列表展示 | 名称/步骤数/包名/启用状态 正确显示 |
| CM-UI-02 | 新建用例对话框 | 填写表单 → 创建 → 列表刷新 |
| CM-UI-03 | 拖拽步骤排序 | 拖拽 → 保存 → 刷新后顺序保持 |
| CM-UI-04 | 从元素定位添加步骤 | 在 elements 页点击"添加为步骤" → 自动填入 |
| CM-UI-05 | 导入 YAML 按钮 | 选择文件 → 确认 → 用例列表新增 |

---

## 变更记录

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.0 | 2026-06-30 | 基于子PRD v1.0 输出，覆盖 10 API + 14 步骤类型 + 5 YAML + 5 UI |
