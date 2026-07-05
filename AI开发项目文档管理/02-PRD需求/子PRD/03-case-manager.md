# 子PRD — 用例工程 (Case Manager)

> 关联模块：`apps/case_manager/` · 前端：`frontend/src/modules/case-manager/`
> 关联全局：`../全局PRD.md` · 关联定位：`../子PRD/01-element-locator.md` · 关联执行：`../子PRD/04-test-runner.md`
> 版本：v2.0 · 状态：草稿 · 日期：2026-06-30

---

## 1. 模块功能目标

用例工程模块是测试平台的测试资产管理中枢，承担以下核心职责：

1. **测试用例定义管理**：创建、编辑、删除、启用/禁用可重用的测试用例定义，包含 14 种步骤类型的结构化编排
2. **测试步骤编排**：通过拖拽排序组合 click / wait / verify_text / sleep 等 14 种原子操作，构建完整的业务流程测试步骤
3. **测试点接入**：从元素定位模块（element-locator）提取标记为 test_point 的元素及其 XPath，作为步骤的定位表达式
4. **YAML 导入导出**：支持将测试用例导出为 YAML 文件、从 YAML 文件导入，实现跨环境迁移和版本管理

### 1.1 模块边界

```
element-locator (XPath + 测试点元素)
      │
      ▼ 提取 Element (is_test_point=True)
case-manager
      │
      ▼ 提供 TestDefinition (steps_json)
test-runner (执行引擎)
```

---

## 2. 功能清单与概述

| 编号 | 功能名称 | 优先级 | 一句话描述 |
|:--:|------|:--:|------|
| F-01 | 用例定义 CRUD | P0 | 创建/编辑/删除/启用-禁用测试用例定义，支持分类和搜索 |
| F-02 | 14 种步骤编排 | P0 | 拖拽排序组合 click / wait / verify_text / sleep 等 14 种步骤类型，构建测试流程 |
| F-03 | 测试点接入与 YAML 导出 | P0 | 从 element-locator 提取测试点元素导出 YAML，支持从 YAML 文件导入用例 |

---

## 3. 功能详细规格

---

### 3.1 F-01：用例定义 CRUD

#### 3.1.1 需求定义

提供测试用例定义的完整生命周期管理：创建（ID/标题/分类/描述/包名）、编辑、删除、启用/禁用、列表查看、搜索筛选。

#### 3.1.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 用例创建数 | 数据库 test_definitions 记录数 | ≥500 |
| 操作响应 | CRUD 操作响应 ≤500ms | 100% |
| 数据一致性 | 删除用例定义不影响已执行的历史结果 | 100% |

#### 3.1.3 触发条件

- 用户进入 case-manager 页面 → 自动加载用例列表
- 用户点击「新建用例」→ 弹出新建对话框
- 用户点击行「编辑」→ 弹出编辑对话框
- 用户点击行「删除」→ 二次确认后删除

#### 3.1.4 业务规则

```
用例定义字段：
- id (必填, 唯一)        : 用例唯一标识，建议格式 "login_test" 或 "category/case_name"
- title (必填)           : 用例标题
- category (可选)        : 分组分类，如 "登录模块"、"支付流程"
- description (可选)     : 详细描述
- steps_json (核心)      : JSON 格式步骤列表（见 F-02）
- enabled (默认 true)    : 是否启用，禁用后执行引擎不加载该用例
- package_name (可选)    : 目标 App 包名（不传则使用全局默认）
- created_at / updated_at: 时间戳
```

**删除约束**：已存在关联执行结果的用例，删除时仅标记 enabled=false（软删除），不做物理删除。

**冲突处理**：同一 id 的用例，保存时执行 update_or_create（幂等）。

#### 3.1.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| 用例列表 | el-table 列：ID / 标题 / 分类 / 步骤数 / 启用状态 / 操作（编辑/删除） |
| 搜索筛选 | 顶部搜索框 + 分类下拉筛选 + 启用状态开关筛选 |
| 新建/编辑对话框 | El-Dialog：ID 输入 / 标题 / 分类 / 描述 / 包名 / 启用开关 |
| 删除确认 | El-MessageBox.confirm："确定删除用例 {title} 吗？" |
| 软删除显示 | enabled=false 的行显示灰色 + 删除线 |

#### 3.1.6 后端接口要求

| 接口 | 核心行为 |
|------|---------|
| `GET /api/cases/definitions` | 列出所有用例定义，解析 steps_json → steps_data。详见附录 §4.3 |
| `POST /api/cases/definitions` | 创建/更新用例定义（update_or_create），body 含所有字段 |
| `GET /api/cases/definitions/{case_id}` | 获取单个用例详情 |
| `DELETE /api/cases/definitions/{case_id}` | 删除用例（检查关联执行结果，有则软删除） |

---

### 3.2 F-02：14 种步骤编排

#### 3.2.1 需求定义

测试用例的核心是步骤序列。用户通过拖拽排序组合 14 种原子步骤类型，构建完整的测试流程。每条步骤包含类型（type）、XPath（xpath/xpath2）、超时（timeout）、预期文本（expected_text）、索引（index）、描述（description）参数。

#### 3.2.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 支持的步骤类型 | 步骤类型枚举数 | 14 种 |
| 步骤编排效率 | 非技术人员 10 分钟内创建 5 步骤用例 | — |
| 步骤数据完整性 | 保存的步骤可被执行引擎正确解析 | 100% |

#### 3.2.3 触发条件

- 用户在 element-locator 页面点击 XPath 的"加入步骤"
- 用户在 case-manager 用例编辑页手动添加步骤
- 用户拖拽步骤调整顺序

#### 3.2.4 业务规则

**14 种步骤类型**：

| # | 步骤类型 | 值 | 参数说明 | 典型场景 |
|---|----------|-----|----------|----------|
| 1 | 点击元素 | `click` | xpath | 点击按钮/链接 |
| 2 | 点击第N个 | `click_indexed` | xpath, index | 列表项点击 |
| 3 | 等待元素出现 | `wait` | xpath, timeout | 等待页面加载完成 |
| 4 | 等待元素出现后消失 | `wait_disappear` | xpath, timeout | 等待加载框消失 |
| 5 | 等待二选一 | `wait_either` | xpath, xpath2, timeout, index | 等待成功/失败二态 |
| 6 | 等待 Toast | `wait_toast` | expected_text, timeout | 验证 Toast 提示 |
| 7 | 验证文本 | `verify_text` | xpath, expected_text | 断言页面内容 |
| 8 | 轮询文本 | `poll_text` | xpath, expected_text, timeout, index | 等待文本变为期望值 |
| 9 | 固定等待 | `sleep` | timeout | 等待几秒 |
| 10 | 杀掉 App | `kill_app` | — | 清理应用状态 |
| 11 | 启动 App | `start_app` | — | 冷启动测试 |
| 12 | 重启 App | `restart_app` | index (kill_wait) | 重启流程测试 |
| 13 | 重试点击 | `retry_click` | xpath, index (retry_max) | 网络波动重试 |
| 14 | 打印日志 | `log` | description | 标记测试阶段 |

**Step 数据结构**：
```json
{
  "type": "click",
  "xpath": "//*[@resource-id='com.example:id/btn_login']",
  "xpath2": "",
  "timeout": 10,
  "expected_text": "",
  "index": 0,
  "description": "点击登录按钮"
}
```

**步骤校验**：
- `type` 必须是 14 种之一
- `click` / `click_indexed` / `wait` / `wait_disappear` / `verify_text` / `poll_text` / `retry_click` 必须有 `xpath`
- `wait_either` 必须有 `xpath` + `xpath2`
- `sleep` 必须有 `timeout`
- `wait_toast` 必须有 `expected_text`

#### 3.2.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| 步骤列表 | 用例编辑页核心区域：拖拽排序列表，每行显示 步骤序号 / 类型图标+名称 / XPath 摘要 / 参数摘要 / 删除按钮 |
| 添加步骤 | 顶部下拉选择步骤类型 + 弹出步骤编辑面板（根据类型动态显示不同字段） |
| 拖拽排序 | vuedraggable 实现步骤重排 |
| XPath 接入 | element-locator 的 XPathTable 中"+"按钮 → 向 case-manager 当前编辑的用例步骤列表追加新步骤 |
| 步骤预览 | 只读模式下展示步骤流程图 |

#### 3.2.6 后端接口要求

| 接口 | 核心行为 |
|------|---------|
| `POST /api/cases/definitions` | 接收完整的 steps_json 字段，直接存储。校验由前端 + 执行引擎加载时完成 |

---

### 3.3 F-03：测试点接入与 YAML 导出

#### 3.3.1 需求定义

从 element-locator 中提取所有标记为 `is_test_point=True` 的元素，结合页面流程（PageFlow）自动生成 YAML 格式的测试用例文件。支持从 exports/ 目录导入已有 YAML 文件。

#### 3.3.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| YAML 导出成功率 | 有测试点元素 → 成功生成 YAML | 100% |
| 导出 YAML 可执行 | 导出的 YAML 可被 test-runner 正确解析和执行 | 100% |

#### 3.3.3 触发条件

- 用户在 case-manager 页面点击「导出 YAML」
- 用户在 case-manager 页面选择已导出文件点击「下载」

#### 3.3.4 业务规则

```
YAML 导出流程：
1. 查询 all Elements WHERE is_test_point=True
2. 按 Page 分组
3. 读取 PageFlow 确定页面跳转顺序
4. 对每个测试点元素：
   - 取 count=1 的 XPath（最优）
   - 生成 click step（如元素 clickable）
   - 生成 wait step（页面跳转后的等待）
5. 输出 YAML 文件到 exports/
6. 同时缓存到 TestCaseCache 表
7. 前端可下载 exports/ 目录下任意文件
```

**导入支持**：
- `GET /api/cases/exports` 列出所有已导出文件
- `GET /api/cases/exports/{filename}` 下载指定文件
- YAML → TestDefinition 的反向导入为 v2 规划

#### 3.3.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| 导出按钮 | 页面顶部「导出 YAML」按钮，点击后 loading → toast 成功 |
| 导出列表 | el-table 列出 exports/ 下 YAML 文件：文件名 / 时间 / 下载按钮 |
| 下载 | 直接 GET `/api/cases/exports/{filename}` 触发浏览器下载 |

#### 3.3.6 后端接口要求

| 接口 | 核心行为 |
|------|---------|
| `POST /api/cases/export/yaml` | 查询 is_test_point 元素 + PageFlow → 生成 YAML → 缓存到 TestCaseCache。详见附录 §4.3 |
| `GET /api/cases/exports` | 列出 exports/ 下文件。详见附录 §4.3 |
| `GET /api/cases/exports/{filename}` | 下载指定文件。详见附录 §4.3 |

---

## 4. 附录

### 4.1 数据模型

#### 4.1.1 cm_test_definitions（测试用例定义）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | CharField(200) | **PK** | 用例唯一标识，建议 "login_test" 格式 |
| `title` | CharField(500) | NOT NULL | 用例标题 |
| `category` | CharField(200) | — | 分组分类 |
| `description` | TextField | — | 详细描述 |
| `steps` | TextField | — | 步骤纯文本描述 |
| `steps_json` | TextField | default='[]' | **结构化步骤 JSON**，执行引擎直接使用 |
| `enabled` | BooleanField | default=True | 是否启用 |
| `package_name` | CharField(200) | — | 目标 App 包名 |
| `created_at` | DateTimeField | auto_now_add | 创建时间 |
| `updated_at` | DateTimeField | auto_now | 更新时间 |

#### 4.1.2 cm_test_cases（YAML 导出缓存）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BigAutoField | PK | 自增主键 |
| `name` | CharField(500) | — | 文件名 |
| `description` | TextField | — | 描述 |
| `yaml_content` | TextField | — | YAML 文本内容 |
| `created_at` | DateTimeField | auto_now_add | 创建时间 |

---

### 4.2 状态说明

| 对象 | 状态 | 含义 |
|------|------|------|
| TestDefinition | enabled=true | 正常可用，执行引擎加载 |
| TestDefinition | enabled=false | 已禁用/软删除，执行引擎跳过 |

---

### 4.3 API 接口规格

| # | 方法 | 路径 | 功能 |
|---|------|------|------|
| 1 | GET/POST | `/api/cases/definitions` | 列出用例 / 创建更新用例 |
| 2 | GET/DELETE | `/api/cases/definitions/{case_id}` | 获取/删除用例 |
| 3 | POST | `/api/cases/export/yaml` | 导出测试点为 YAML |
| 4 | GET | `/api/cases/exports` | 列出导出文件 |
| 5 | GET | `/api/cases/exports/{filename}` | 下载导出文件 |

**POST /api/cases/definitions** (创建/更新用例)

Request:
```json
{
  "id": "login_test",
  "title": "登录流程测试",
  "category": "用户模块",
  "description": "验证用户名密码登录流程",
  "enabled": true,
  "package_name": "com.example.app",
  "steps_json": "[{\"type\":\"click\",\"xpath\":\"//*[@resource-id='com.example:id/btn_login']\",\"description\":\"点击登录\"},{\"type\":\"wait\",\"xpath\":\"//*[@text='首页']\",\"timeout\":5}]"
}
```

Response 200:
```json
{
  "ok": true,
  "id": "login_test",
  "title": "登录流程测试",
  "steps_data": [
    {"type": "click", "xpath": "//*[@resource-id='com.example:id/btn_login']", "description": "点击登录"},
    {"type": "wait", "xpath": "//*[@text='首页']", "timeout": 5}
  ]
}
```

---

### 4.4 非功能需求

| 类别 | 指标 | 目标值 |
|------|------|:--:|
| **数据容量** | 用例定义数 | ≥500 |
| **数据容量** | 单用例步骤数 | ≥50 |
| **性能** | 列表查询 | ≤500ms |
| **数据一致性** | YAML 导出可被 test-runner 执行 | 100% |

---

### 4.5 非目标（Non-goals）

| 功能 | 原因 | 归属 |
|------|------|------|
| 用例版本管理/回滚 | 当前按 YAML 导出实现离线版本管理 | v3 |
| BDD/Gherkin 语法 | 非核心需求 | v4 |
| 数据驱动测试（参数化） | 执行引擎 v3 支持 | test-runner v3 |
| AI 自动生成用例 | 依赖 AI 能力 | ai-assistant v4 |
| 用例评审/审批流 | 非测试工具核心 | v4 |

---

### 4.6 里程碑

| 阶段 | 交付物 | 对应功能 |
|------|------|----------|
| v1 ✅ | 用例 CRUD + 14 种步骤存储 + YAML 导出 | F-01, F-02, F-03 |
| v2 当前 | 拖拽排序 UI + 步骤模板 + 批量操作 | UI 增强 |
| v3 | 用例版本管理 + 参数化 | — |

---

## 变更记录

| 版本 | 日期 | 变更类型 | 变更摘要 |
|------|------|----------|----------|
| v1.0 | 2026-06-30 | — | v1 实现完成：CRUD + YAML 导出 |
| v2.0 | 2026-06-30 | 重写 | 统一 6 维度结构，补充业务规则和步骤校验规则 |
