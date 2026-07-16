---
name: auto-dev
description: |
  自动开发编排器 — 用户提需求，AI 自动完成探索→方案→编码→审查→测试全流程。
  三档强度（Lite/Standard/Strict）根据任务复杂度自动选择，workflow-manifest.json 跨阶段追踪状态。
  Keywords: 开发, 实现, 做, 改, 修, 加, 新增, 删除, 优化, 重构, 写代码, 帮我做, 帮我改, develop, implement, build, fix, create, auto
  Trigger: 用户表达开发需求时自动激活。含"帮我做/实现/开发/修改/新增/修复/优化/重构 + 具体文件或功能"等关键词。
---

# Auto-Dev — AI 自动开发编排器

**一句话**: 你提需求，我出方案，你点头，我全自动执行到交付。

**设计哲学**: Planning Agent（只研究不执行）→ 方案确认 → Developer Agent（执行+自查）→ 交付报告。

## 三档强度

| 强度 | 触发条件 | 阶段序列 | 审查深度 | 报告 |
|------|---------|---------|---------|------|
| 🪶 **Lite** | 1文件≤50行 / 修Bug / 改文案 / 加注释 / 加类型注解 | 探索→方案→编码→Review | 终端打印 | 无HTML |
| 🛡️ **Standard** | 2-3文件 50-200行 / 单模块功能增删 | 探索→方案→编码→Review→测试 | quality-gate 齿轮1+2 | HTML |
| 🏛️ **Strict** | 新模块 / 跨模块 / API变更 / 3+文件 / >200行 | 探索→方案→编码→Review→测试→架构审查 | quality-gate 全齿轮 | HTML×2 |

## 工作流

### Phase -1: 需求提炼（用户输入模糊时触发）

**触发条件**: 用户需求缺以下任一要素:
- 没有指明具体功能模块（"有点问题"、"不好用"）
- 没有指明具体文件或组件
- 描述的是感受而非技术问题（"太慢了"、"体验不好"）

**不触发**: 用户已指明具体文件/函数/组件 + 具体要做什么 → 跳过，直接 Phase 0

**提炼流程**:

```
用户模糊输入 ("Agent创建有点问题" / "仪表盘太慢")
  ↓
Step -1.1: 领域映射
  将用户语言映射到平台模块和可能的技术根因:

  | 用户说的 | 可能涉及的模块 | 可能的技术根因 |
  |---------|-------------|-------------|
  | "Agent创建/管理/配置有问题" | ai_assistant / agent_factory / AgentDetail.vue | API Key解密/权限校验/AgentScope注册/前端保存逻辑 |
  | "仪表盘/首页太慢/不显示" | dashboard / views.py | N+1查询/无缓存/API超时 |
  | "截图/元素定位不显示" | element_locator / pool.py / ScreenshotConsumer | ADB连接/u2崩溃/WS握手/截图流断开 |
  | "设备连不上/离线" | device_pool / pool.py / ADB | USB断连/u2连接超时/ATX Agent未运行 |
  | "执行/跑用例失败" | test_runner / adapter.py / executor.py | u2操作超时/元素未找到/设备锁超时 |
  | "AI对话无响应" | ai_assistant / AgentScope / Redis | Redis断连/API Key过期/AgentScope未启动 |
  | "保存/删除没反应" | 对应模块的 views.py / api.js / CaseEditor.vue | 前端catch吞错/后端500/权限校验 |
  | "页面白屏/加载不出来" | Vite / router.js / 对应index.vue | 语法错误/动态import失败/模块500 |

  映射知识来源: .claude/rules/troubleshooting.md 速查表 / architecture.md / database.md

  ↓
Step -1.2: 快速探索（只读，定位根因）
  并行执行:
  - grep 关键词 .claude/rules/troubleshooting.md → 匹配已知问题模式
  - grep ERROR logs/backend.log → 找相关错误日志
  - grep 关键词 apps/ → 找相关代码文件
  - 检查 CLAUDE.md 历史高频问题表 → 是否是已知重复问题

  ↓
Step -1.3: 提炼为具体需求
  将模糊输入 + 探索结果 → 输出 1-3 个具体候选方案:

  "你提到'Agent创建有点问题'，探索后发现 3 个可能方向:

   🔴 方案A: 修复 agent_factory.py 异常处理
      - decrypt_key() 无 try/except
      - AIAgent.objects.get() 无 try
      - user_id 未消费 → 权限校验缺失
      涉及: 1文件 / 预估15行 / 约10分钟

   🟠 方案B: 检查 AgentScope 注册流程
      - agent_scope_id 为空时是否降级
      涉及: 1文件 / 预估5行 / 约5分钟

   🟡 方案C: 检查前端 AgentDetail 保存逻辑
      - 保存失败是否有错误提示
      涉及: 1文件 / 预估8行 / 约8分钟

   建议先做 A（P0安全+稳定性），再做 B。你觉得？"

  ↓
Step -1.4: 用户选择 → 确定需求 → 初始化 manifest → 进入 Phase 0
```

**关键原则**:
- 提炼需求时必须基于真实代码探索，不能凭空猜测
- 每个方案标注涉及文件和预估时间
- 给出具体方案对比而非开放式问题
- 用户选择后立即进入 Phase 0，不再重复探索

### Phase 0: 复杂度判定（必须执行的探索）

**原则**: Planning Agent 模式 — 先研究，不执行。

```
用户需求
  ↓
Step 0.1: 并行启动 2-3 个只读探索任务
  任务A: 定位目标 → Read 入口文件 → 列出受影响函数/类
  任务B: 追踪依赖 → grep 跨模块 import → 发现上下游
  任务C: 关键字搜索 → grep 需求关键词 → 发现隐藏关联
  ↓
Step 0.2: 汇总探索结果
  - 涉及文件数 / 函数数 / 模块数
  - 是否涉及 API 签名变更
  - 是否涉及数据库表结构变更
  - 是否有跨模块影响
  - 预估代码变更行数
  ↓
Step 0.3: 规则引擎判定强度
  IF 新增模块/App/数据库表 → Strict
  IF API 端点签名变更 → Strict
  IF 跨模块 import 变更 → Strict
  IF 文件>3 AND 行数>200 → Strict
  IF 文件2-3 AND 行数50-200 → Standard
  IF 单文件 AND 函数>3 → Standard
  IF 单文件 AND ≤50行 AND 单函数 → Lite
  IF 修Bug/改文案/加注释/加类型注解 → Lite
  DEFAULT → Standard (置信度:低，提供对比方案让用户选)
  ↓
Step 0.4: 置信度低时出对比方案
  "这个任务涉及 X 个文件。方案A(Lite/5min)风险是... 方案B(Standard/15min)覆盖更全。建议选B，你觉得？"
  ↓
Step 0.5: 初始化 workflow-manifest.json
  在 plans/{task-slug}/ 下创建 manifest，写入 intake 阶段状态
```

### Phase 1: 方案输出（必须用户确认）

```
根据探索结果生成实施计划:
  - 目标: 1-2句话
  - 涉及文件: 精确路径 × 改动类型(Create/Modify/Delete)
  - 实施步骤: P0/P1 分级，每步标注预估时间
  - 风险: 标注不确定点
  - 验证: 如何确认完成

输出方式: EnterPlanMode → 等用户审批
manifest 更新: phase=plan, status=pending_approval
```

### Phase 2: 代码执行

```
用户批准后自动执行，不再询问:
  Step 2.1: 按方案逐文件修改 (Edit/Write)
  Step 2.2: ruff format + prettier 格式化
  Step 2.3: 编译检查 (vite build / python manage.py check)
    ├── 通过 → 继续
    └── 失败 → 自动修复 (最多3次)
         ├── 修复成功 → 继续
         └── 3次失败 → 暂停，报告原因，等用户介入
  Step 2.4: manifest 更新 → phase=code, status=done
```

### Phase 3: 代码审查

```
按强度选择审查深度:
  Lite:
    code-health-check 引擎1(ruff) + 关键语义检查(魔法值/异常吞噬)
    终端打印结果
  
  Standard:
    quality-gate 齿轮1(写法) + 齿轮2(契约)
    输出 HTML 到 tests/functional/{module}/reports/
  
  Strict:
    quality-gate 全四齿轮
    输出 HTML + 架构审查报告
    如发现 P0 安全/权限问题 → 暂停，报告用户

manifest 更新 → phase=review, status=done, p0_count=N
```

### Phase 4: 测试验证

```
Step 4.1: 环境探测 (5秒)
  redis-cli ping → PONG/FAIL
  adb devices    → 有/无设备
  curl :8765/api/ → 200/FAIL
  curl :8000/docs → 200/FAIL

Step 4.2: 分级执行
  ┌──────────────────────────────────────────┐
  │ 全就绪: 静态 + API接口 + 端到端            │
  │ Django就绪,无设备: 静态 + API格式校验       │
  │ 全不可用: 仅静态分析 + 编译检查             │
  └──────────────────────────────────────────┘

  所有等级（包括"全不可用"）**必须执行 API 数据契约往返校验**：
    哪怕 Django 不在运行，只要改动涉及「前端表单组件 + 后端 API」的数据传递，
    就必须在代码层面检查：
    a. 前端组件 v-model 的输出类型（查组件文档默认值）
    b. 后端 views.py 期望的字段类型（直接读代码）
    c. 两者是否一致？不一致 → 标记为 P0，暂停

Step 4.3: 向用户报告 + 建议
  "测试结果: 静态检查✅ / API测试跳过⚠️(Django未启动) / 端到端跳过⚠️(无设备)
   建议: A.启动服务重测 B.接受静态结果继续 C.跳过测试直接交付"

manifest 更新 → phase=test, status=done, env=全就绪/部分/不可用
```

### Phase 5: 交付

```
输出最终报告 (HTML, 仅 Standard/Strict):
  - 执行摘要 (改了什么/几行/几个文件)
  - 审查结果 (发现问题数/P0数)
  - 测试结果 (通过/跳过/失败)
  - manifest 完整状态

manifest 更新 → status=completed
```

### Feedback Phase: 用户反馈排查（交付后触发）

**触发条件**: Phase 5 交付后，用户反馈:
- "不对，XX 功能没实现"
- "我看到的是 YY，不是预期的 ZZ"
- "点 XX 没反应" / "数据没刷新" / "页面白屏"

**排查流程**:

```
用户反馈 (UI 表象)
  ↓
F1. 症状分类 → 选择排查路径

  症状: "点按钮没反应"
    → 优先查: 前端事件绑定 / Network 面板看请求是否发出 / Console 报错
    → 次查: 后端是否收到请求 / 返回了什么

  症状: "数据不对/没刷新"
    → 优先查: API 返回了什么 / 前端字段映射是否正确
    → 次查: ORM 查询条件 / 数据库实际值

  症状: "页面白屏/报错"
    → 优先查: Vite 编译 / Vue 语法 / 动态 import 失败
    → 次查: CDN/依赖加载

  症状: "功能完全没生效"
    → 优先查: 路由是否注册 / 中间件是否拦截 / 是否有条件分支跳过

  ↓
F2. 四层下钻排查

  层1: 浏览器 (前端表象)
    检查: DevTools Console / Network 面板 / Vue DevTools
    命令: 浏览器手动操作 + 观察
    发现: JS报错 / API状态码 / 请求是否发出 / 响应内容

  层2: 前端编译
    检查: 模块加载 / 语法错误
    命令: curl -s -o /dev/null -w "%{http_code}" :5173/src/modules/{name}/index.vue
          npx vite build --mode development 2>&1 | tail -10
    发现: HTTP 500 / 语法错误 / import 失败

  层3: API 层
    检查: 后端是否收到请求 / 返回了什么
    命令: curl -s :8765/api/{endpoint} | python -m json.tool
          tail -50 logs/backend.log | grep ERROR
    发现: 404/500 / 响应格式不对 / 字段缺失

  层4: 数据库
    检查: 数据是否真的写入了
    命令: python manage.py shell -c "from apps.{app}.models import X; print(X.objects.filter(...))"
    发现: 数据未写入 / 字段值错误 / 查询条件不匹配

  ↓
F3. 输出排查报告 + 修复方案

  "问题定位:
   根因: AgentDetail.vue 保存时 catch 块吞掉了错误，后端返回 500 但前端没提示
   证据: Network 面板显示 POST /api/ai/agents/create 返回 500
         logs/backend.log 显示 decrypt_key() InvalidToken

   修复方案:
   1. agent_factory.py L110: except Exception 过宽 → 改为 except InvalidToken
   2. AgentDetail.vue save(): catch 加 ElMessage.error

   涉及: 2文件 / 预估10行 / 约8分钟。要修吗？"

  ↓
F4. 用户确认 → 进入 Phase 1 (方案) → 正常流水线
```

**四层排查工具链**:

| 层 | 检查命令 | 能发现什么 |
|------|---------|-----------|
| 浏览器 | DevTools Console / Network 面板 | JS 报错、API 状态码、请求是否发出 |
| 前端编译 | `npx vite build 2>&1` | 语法错误、模块加载失败 |
| API | `curl -s :8765/api/xxx` | 响应格式、状态码、字段完整性 |
| 后端日志 | `tail -100 logs/backend.log` | Django 异常、ORM 错误 |
| 数据库 | `python manage.py shell` + ORM 查询 | 数据是否真的写入了 |

## Workflow Manifest

每个任务在 `plans/{task-slug}/` 下维护状态文件：

```json
{
  "task": "agent_factory_add_try_except",
  "created": "2026-07-05T14:30:00",
  "intensity": "standard",
  "stages": {
    "intake":    {"status": "done", "files": 1, "confidence": "high"},
    "plan":      {"doc": "plans/xxx/plan.md", "status": "approved"},
    "code":      {"files": ["agent_factory.py"], "lines_changed": 25, "status": "done"},
    "review":    {"report": "reports/quality_gate.html", "p0": 0, "p1": 2, "status": "done"},
    "test":      {"report": "reports/test.html", "env": "partial", "passed": 12, "skipped": 5, "status": "done"}
  },
  "delivery": {
    "report": "tests/functional/{module}/reports/{task}-report.html",
    "completed": "2026-07-05T14:55:00"
  }
}
```

详细规范见 `references/manifest-spec.md`。

## 用户确认点

只保留 2 个必须确认的时刻:

1. **方案审批** (Phase 1→2) — 无论档位，必须等用户说"可以"
2. **P0 安全暂停** (Phase 3) — quality-gate 发现 P0 问题时暂停

其他环节全自动推进。

## 失败回退策略

```
编译失败 → 自动修(3次) → 再失败 → 暂停+报告
审查发现P0 → 暂停+修复建议 → 等用户决定
测试环境不可用 → 跳过+标注 → 不阻塞
测试失败 → 分析原因+尝试修复(1次) → 再跑 → 仍失败则报告
```

## 关联文件

| 文件 | 用途 |
|------|------|
| `references/manifest-spec.md` | Workflow Manifest 完整规范 |
| `references/gate-checklist.md` | 三级 Gate 检查清单 |
| `../code-health-check/SKILL.md` | 内置引擎 写法层 |
| `../quality-gate/SKILL.md` | 内置引擎 全量审查 |
| `../functional-testing/SKILL.md` | 内置引擎 功能测试 |
| `../feature-analysis/SKILL.md` | Strict 模式业务分析 |
| `html-report` skill | HTML 报告 design token，生成报告时加载 |
