---
name: architecture-review
description: |
  架构审查 — 分析项目模块化程度，检查高内聚低耦合，绘制理想架构图，对比实际差距，输出实施建议。
  Keywords: 架构审查, 模块化分析, 架构图, 模块依赖, 高内聚低耦合, architecture review, 依赖分析, 分层设计
  Trigger: 用户表达"审查架构/分析模块/画架构图/模块化设计/依赖关系"时。
---

# Architecture Review

**目的**: 在模块化拆分或重构前，先审查现状 — 找出高内聚低耦合问题、分层违规、安全缺口。

**能力模型**: 绘制(Draw) → 对比(Compare) → 报告(Report) → 建议(Suggest)

## 五维审查模型

| 维度 | 检查什么 | 典型问题 |
|------|------|------|
| **高内聚** | 模块内功能是否紧密相关？有无错位的代码？ | dashboard 代码在 ai_assistant 中 |
| **低耦合** | 跨模块 import 是否走 api.py？是否有循环依赖？ | 直接 import 内部实现而非 api 白名单 |
| **分层合理** | 依赖方向是否单向？层级是否清晰？ | 底层模块依赖上层模块 |
| **安全完整** | WebSocket 有认证吗？凭据是否硬编码？ | WS connect() 无 JWT 验证 |
| **一致性** | 模块结构是否统一？命名是否规范？ | 有的模块缺 api.js，有的缺 serializers.py |

> 详细判断标准见 `references/analysis-checklist.md`。

## 工作流

### Phase 1: Draw — 绘制理想架构图

#### 1.1 设计原则（先判断，后绘制）

**原则一：模块边界 = 数据主权**

模块边界由"谁拥有这张表"决定。一个模块 = 一套数据库表 + 操作这些表的 API。

```
判断标准: 表前缀归属 → dp_ 属于 device_pool，ai_ 属于 ai_assistant
反例: dashboard 操作其他模块的表 → 它不拥有表 → 是聚合层，不是独立业务模块
```

**原则二：层级 = 被依赖程度**

谁都不依赖的放底层，被所有人依赖的放顶层。层级反映的是依赖方向，不是重要性。

```
底层 (L3-bottom): 零依赖 — 只有被依赖，从不依赖别人
  device_pool, report_generator

中层 (L3-middle): 只依赖底层 — 依赖少，被依赖多
  element_locator (→ DP), case_manager (→ EL), test_runner (→ DP+CM+RG)

聚合层 (L3-top): 依赖所有下层 — 自身无表或只有配置表
  ai_assistant (→ 5 Apps), dashboard (→ 5 Apps, 只读)
```

**原则三：同级模块必须对等**

同一层的模块应该在"体量"上相当 — 不能一个模块 3 张表 50 端点，另一个只有 1 个脚本。

```
检测方法: 数每个模块的 models.py 中 class 数、urls.py 中 endpoint 数
异常信号: 某模块的代码行数是同级模块的 5 倍以上 → 可能需要拆分
```

**原则四：依赖只向下，跨层走接口**

上层可以依赖下层，下层绝不能依赖上层。跨层通信只能通过 api.py 白名单，不能直接 import 内部实现。

```
✅ ai_assistant → device_pool (合理，聚合层依赖底层)
❌ device_pool → ai_assistant (违规，底层不应该知道上层存在)
✅ 跨模块写: from apps.device_pool.api import acquire_device
❌ 跨模块写: from apps.device_pool.views import lock_device
```

**原则五：通信协议由数据特性决定**

| 场景 | 协议 | 为什么 |
|------|------|--------|
| 请求-响应（CRUD） | HTTP REST | 无状态，可缓存，标准工具链 |
| 服务端主动推送（实时数据） | WebSocket | 长连接，双向，低延迟 |
| 服务端流式输出（AI 对话） | SSE | 单向流，自动重连，浏览器原生支持 |
| 同进程内调用 | 直接函数调用 | 零网络开销，类型安全 |
| 异步任务 | Redis / 数据库轮询 | 解耦生产者和消费者 |

#### 1.2 绘制步骤

```
Step 1: 从数据出发，确定模块清单
  → 列出所有数据库表，按前缀分组 → 每组 = 一个模块
  → 无表的模块（dashboard）→ 审视是否有独立存在的必要

Step 2: 分析依赖，确定层级
  → 搜索跨模块 import: grep -rn "from apps\." apps/
  → 画出依赖图，从被依赖最多的模块开始排（底层），逐步往上

Step 3: 放置模块到四层架构中
  L1 前端:    7 个 Vue 模块，对应 7 个后端 App
  L2 网关:    JWT 中间件 / URL Router / WS Router
  L3 业务:    底层(2) → 中层(3) → 聚合层(2)
  L4 基础设施: MySQL / Redis / AgentScope / uiautomator2

Step 4: 标注通信方式
  层间连线标注协议，关键路径标注接口函数名

Step 5: 自检
  - [ ] 每个模块是否拥有明确的数据主权（表前缀）？
  - [ ] 依赖方向是否全部单向向下？
  - [ ] 同级模块体量是否对等（代码行数/端点数在同一量级）？
  - [ ] 是否有模块只有 1-2 个函数？→ 考虑合并
  - [ ] 是否有模块横跨 5+ 个外部依赖？→ 考虑拆分或明确聚合层身份
  - [ ] 层级是否控制在 3-4 层？
```

### Phase 2: Compare — 对比实际架构

```bash
# 1. 扫描跨模块 import（发现违规依赖）
grep -rn "from apps\." apps/ --include="*.py" | grep -v migrations

# 2. 检查是否绕过 api.py 直接 import 内部实现
grep -rn "from apps\..*\.views import\|from apps\..*\.service import" .

# 3. 检查前端模块是否有无后端对应的冗余
ls frontend/src/modules/  # 与 config/settings.py 对照

# 4. 检查 WebSocket 安全
grep -rn "def connect" apps/*/consumers.py | grep -v "token\|jwt\|verify"

# 5. 检查模块结构完整性
for app in device_pool element_locator case_manager test_runner report_generator ai_assistant dashboard workflow; do
  for f in api.py serializers.py permissions.py; do
    [ -f "apps/$app/$f" ] || echo "MISSING: apps/$app/$f"
  done
done

# 6. 检查前端 api.js 完整性
for mod in dashboard device-pool element-locator case-manager test-runner report-generator ai-assistant workflow; do
  [ -f "frontend/src/modules/$mod/api.js" ] || echo "MISSING: $mod/api.js"
done
```

### Phase 3: Report — 生成 HTML 报告

```bash
python .Codex/skills/architecture-review/scripts/report_generator.py \
  --output dev_docs/03-设计与架构/架构审查报告.html
```

报告内容:
- **KPI 摘要**: 模块数 / 问题数 / 实施周期估计
- **理想架构图**: 4 层模块卡片 + 依赖标注 + 通信方式
- **差距对照表**: 问题 → 严重度 → 修复方案
- **实施路线**: P0/P1/P2 分级任务

样式与 `modules/模块化架构设计方案.html` 一致: animal-island-ui 13 色调色板、Nunito 字体、24px 大圆角。

### Phase 4: Suggest — 实施建议

```
1. 按 P0/P1/P2 分级:
   P0 — 影响安全或导致模块混乱，必须修复
   P1 — 影响可维护性或扩展性，建议修复
   P2 — 代码风格或最佳实践，择机修复

2. 每项给:
   - 具体文件路径
   - 修改方式（新建/迁移/删除/修改）
   - 影响范围

3. 输出验证清单:
   - grep/curl 检查项
   - 编译/启动验证
```

## 关联文件

| 文件 | 何时加载 |
|------|---------|
| `references/analysis-checklist.md` | 执行 Phase 2 时加载 |
| `scripts/report_generator.py` | 生成 HTML 报告时调用 |
| 已有的 `dev_docs/03-设计与架构/html/总设计-模块化架构设计方案.html` | 作为报告模板参考 |
| `html-report` skill | 生成 HTML 报告时加载 design token |

## 输出位置

`dev_docs/03-设计与架构/架构审查报告_{timestamp}.html`
