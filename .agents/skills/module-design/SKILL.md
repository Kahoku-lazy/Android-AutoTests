---
name: module-design
description: |
  模块化设计 — 将复杂系统拆分为更小、更易管理的模块，通过代码封装和接口抽象减少模块间依赖，统一目录结构和命名规范。
  Keywords: 模块化, 模块拆分, 目录结构, 命名规范, 代码规范, 接口抽象, 防火墙, module design, modularization
  Trigger: 用户表达"模块化设计/模块划分/统一规范/目录结构/代码规范/命名约定/降低耦合"时。
---

# Module Design — 模块化设计与代码规范

**目的**: 将复杂系统拆分为高内聚、低耦合的模块，统一代码风格，降低维护成本。

**能力模型**: 梳理(Inventory) → 划分(Partition) → 规范(Standardize) → 清理(Cleanup)

## 核心原则

```
高内聚: 同一模块内的功能高度相关，一个模块只做一件事
低耦合: 不同模块间尽量独立，通过接口抽象减少直接依赖
单向依赖: 依赖方向从上层到下层，禁止循环依赖
接口隔离: 跨模块写操作只能调用 api.py 白名单函数
```

## 工作流

### Phase 1: Inventory — 梳理现状

```
1. 绘制完整目录树
   find . -type f | grep -v node_modules | grep -v .venv | grep -v __pycache__

2. 分析跨模块依赖
   grep -rn "from apps\." apps/ --include="*.py" | grep -v migrations

3. 检查模块结构完整性
   后端: 每个 App 是否有 api.py / serializers.py / permissions.py？
   前端: 每个模块是否有 api.js / routes.js？

4. 检查命名一致性
   grep -rn "ONLINE\|BUSY\|OFFLINE" apps/  → 状态值是否硬编码？
   grep -rn "import client from" frontend/src/ → 是否绕过 api.js？

5. 识别问题列表:
   - 功能重叠的模块
   - 职责错位的代码
   - 空壳/死代码
   - 循环依赖
```

### Phase 2: Partition — 模块划分

```
1. 确定模块清单 → 按业务领域划分，每个模块独立可部署

2. 绘制依赖图 → 底层模块（零依赖）→ 中间模块 → 聚合层
   规则: 依赖方向必须单向，禁止循环

3. 定义模块边界:
   - 每个模块有自己的数据库表前缀
   - 每个模块有自己的 URL 前缀
   - 跨模块通信只能通过 api.py

4. 合并重叠模块 → 功能重叠的前端模块合并为子视图

5. 移除空壳 → 已注册但无代码的 App 从 INSTALLED_APPS 移除
```

### Phase 3: Standardize — 统一规范

#### 后端 App 标准结构

```
apps/{app_name}/
├── __init__.py          # 必须
├── models.py            # 必须 — Meta.db_table 显式表名
├── views.py             # 必须 — HTTP 入口，只做参数解析和响应
├── api.py               # 必须 — __all__ 白名单，跨模块写操作
├── urls.py              # 必须 — app_name + urlpatterns
├── apps.py              # Django 自动生成
├── admin.py             # 必须
├── serializers.py       # 必须 — 输入校验 + 输出格式化
├── permissions.py       # 必须 — 权限检查
├── service.py           # 可选 — 内部业务逻辑
├── consumers.py         # 可选 — WebSocket
└── migrations/          # 自动管理
```

#### 前端模块标准结构

```
frontend/src/modules/{module-name}/
├── index.vue            # 必须 — 模块主页
├── routes.js            # 必须 — 子路由定义
├── api.js               # 必须 — 封装 API 调用，禁止直接 import client
├── store.js             # 可选 — 状态管理
├── composables/         # 可选 — 可组合逻辑
└── components/          # 可选 — 模块内组件
```

#### 命名规范（9 层对照）

| 层级 | 规范 | 示例 |
|------|------|------|
| Python 文件/变量/函数 | `snake_case` | `device_pool`, `get_device()` |
| Python 类 | `PascalCase` | `DevicePool`, `StepExecutor` |
| JS 文件/变量/函数 | `camelCase` | `apiClient`, `getDevices()` |
| Vue 组件文件 | `PascalCase.vue` | `AgentDetail.vue` |
| Vue 模板中 | `kebab-case` | `<device-pool>` |
| API URL | `kebab-case` | `/api/device-pool/` |
| JSON 字段 | `snake_case` | `{"test_case_id": 1}` |
| 数据库表 | `{prefix}_snake_case` | `dp_devices`, `cm_test_cases` |
| CSS class | `kebab-case` | `.device-card` |

#### 数据库表前缀

| 前缀 | 模块 |
|------|------|
| `dp_` | device-pool |
| `el_` | element-locator |
| `cm_` | case-manager |
| `tr_` | test-runner |
| `rg_` | report-generator |
| `ai_` | ai-assistant |

#### 状态值规范

禁止硬编码状态字符串，统一使用 `models/constants.py` 中的 Enum:

```python
from models.constants import DeviceStatus, TestRunStatus

device.status = DeviceStatus.ONLINE  # ✅
device.status = "ONLINE"             # ❌
```

#### 跨模块三道防火墙

```
防火墙 #1: service.py 互不 import
  ✅ 跨 App import Model（只读）+ api.py（写操作）
  ❌ 跨 App import service / 内部实现

防火墙 #2: 读放开，写收敛
  ✅ 跨 App 读: 直接 ORM
  ❌ 跨 App 写: 必须走 api 函数

防火墙 #3: 外部访问只走 API
  Vue → HTTP → Django API → ORM → DB
  AgentScope → Tool → Django ORM/API（同进程）
```

#### API 调用封装强制规则

```js
// ✅ 正确 — api.js
import client from '@/shared/api-client.js'
export function listDevices() { return client.get('/devices') }

// ❌ 错误 — 组件中直接调用
import client from '@/shared/api-client.js'
const { data } = await client.get('/devices')
```

### Phase 4: Cleanup — 实施清理

```
清理顺序（由易到难，每步验证）:

1. 删除死代码
   - 空壳 App（无 models 的 project_hub / requirement_tracker）
   - 旧版前端（_legacy/）
   - 未使用的 wsgi.py

2. 合并重叠模块
   - element-manager → element-locator（前端）

3. 拆分错位代码
   - dashboard → 从 ai_assistant 提取为独立 App

4. 补齐缺失文件
   - 后端: api.py / serializers.py / permissions.py
   - 前端: api.js

5. 安全加固
   - WebSocket JWT 认证
   - 硬编码凭据替换

6. 三层变更检查 🔴 必检
   每个模块操作必须同步更新三层，缺一不可:

   操作 → 架构层 (代码)  +  路由层 (桥梁)  +  交互层 (UI)
   ─────────────────────────────────────────────────────────
   合并  → 移动文件删旧目录  +  合并 routes.js  +  侧边栏减项+Tab子视图
   拆分  → 新建目录复制文件  +  新增 routes.js  +  侧边栏加项+独立页面
   删除  → 删除目录移除注册  +  移除路由      +  侧边栏删项
   新增  → 新建 App 标准文件  +  注册路由      +  侧边栏加项+入口页面

   检查命令:
   - 侧边栏一致性: grep "path:" frontend/src/shared/components/AppSidebar.vue
   - 路由残留: grep -r "旧模块名" frontend/src/router.js
   - 合并后 Tab 入口: grep "Tabs\|activeTab" frontend/src/modules/{parent}/index.vue

7. 验证
   - npx vite build
   - python manage.py check
   - python run.py start
```

## 关联文件

| 文件 | 何时加载 |
|------|---------|
| `references/module-template.md` | 新建模块时加载，提供文件模板 |
| `models/constants.py` | 定义状态 Enum 时引用 |
| `android-autotests-rules/references/conventions.md` | 命名规范速查 |
| `android-autotests-rules/references/api-conventions.md` | 跨模块通信规则 |

## 与 architecture-review 的配合

```
architecture-review: 诊断问题 → 输出报告
        ↓
module-design:       设计方案 → 实施整改
```
