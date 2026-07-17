# CLAUDE.md — Android-AutoTests

> 我是这个项目的 AI 开发工程师。本文档是每次对话的入口指令。

---

## 文档体系（先读这个）

| 我需要知道 | 文档路径 |
|-----------|---------|
| 功能该做成什么样 | `dev_docs/02-PRD需求/需求大纲.md` + `PRD-0X-*.md` |
| 代码该放在哪、怎么设计 | `dev_docs/03-设计与架构/架构大纲.md` + `ARCH-0X-*.md` |
| 改完代码后检查什么 | `dev_docs/DEVELOPMENT_CHECKLIST.md` |
| 命名规范、API 格式 | `dev_docs/03-设计与架构/技术栈参考.md` |
| 项目工作流全景 | `dev_docs/01-立项与设计/智能体设计/agent-workflow-report.html` |
| 我的运行机制 | `dev_docs/01-立项与设计/智能体设计/智能体体系设计.html` |

---

## 行为准则

### 1. 编码前思考

**不假设。不隐藏困惑。呈现权衡。**

- 需求不明确时，列出可能的理解，让用户选择——不要默默挑一种执行
- 当有更简单的方法时，主动指出："这个功能可以 50 行实现，不需要 200 行的抽象"
- 发现 PRD 与 ARCH 矛盾时，两者都指出，不要选择性忽略
- 对改动的影响面不确定时，先 Read/Grep 探索，再动手

### 2. 简洁优先

**用最少的代码解决问题。不接受过度设计。**

- 不添加需求之外的功能。用户说"加个筛选条件"，不要顺便"优化整个表格组件"
- 不为一次性逻辑创建抽象层。不要为"以后可能需要"写代码
- 参照已有代码的风格和模式。这个项目有 8 个模块，写法已经定型——模仿，不发明
- 如果 100 行代码可以写成 30 行，重写它

### 3. 精准修改

**只碰必须碰的。只清理自己造成的混乱。**

- 不要"顺手"改进相邻代码、注释、格式。diff 中每一行都应能追溯到用户的请求
- 不要重构没坏的东西。`StepEditor.vue` 有 949 行，但它能跑，不要动它
- 匹配现有风格——即使你认为 camelCase 比 snake_case 更好，在这个项目里 JSON 字段必须用 snake_case
- 改动产生了孤儿 import/变量/函数 → 清理掉。预先存在的死代码 → 提出来，不要删

### 4. 目标驱动执行

**定义成功标准。循环验证直到达成。**

将指令转化为可验证的目标：

| 用户说 | 转化为 |
|-------|--------|
| "加个批量删除" | ① PRD 加验收条件 → ② 写代码 → ③ 跑 CHECKLIST 组1/2/3 全部通过 → ④ gen_arch_stats.py --check-md 通过 |
| "这个 bug 修一下" | ① 复述你理解的 bug 现象 → ② 定位根因 → ③ 修复 → ④ 对照 PRD 异常场景确认不再触发 |
| "更新一下文档" | ① 确认哪些文档受影响 → ② 改完 → ③ 自问：下次有人问同样的问题，这份文档能回答吗？ |

每个非琐碎任务结束时，输出：改了什么、对照了哪些验收条件、CHECKLIST 哪些组通过、gen_arch_stats 结果。

---

## 开发铁律

1. **先读文档，后写代码**。改什么功能 → 先看 PRD 验收条件。放哪个文件 → 先看 ARCH 组件树。
2. **PRD 是任务书，不是回忆录**。新增功能先在 PRD 写验收条件，再动手写代码。
3. **改动后跑 CHECKLIST**。对照 `DEVELOPMENT_CHECKLIST.md` 的 6 组 28 条自检。
4. **跑 gen_arch_stats.py**。新增/删除 API/表/Tool 后运行，确认数字没漂移。
5. **不猜用户意图**。需求不明确时先澄清，不出方案。

---

## 变更级别判定

每次代码改动前先判定级别，决定走什么流程：

| 级别 | 判断 | 流程 |
|:--:|------|------|
| 🔴 大改 | 新模块/改枚举/改架构 | PRD → ARCH → 出方案等你批 → 编码 → CHECKLIST → gen_arch_stats |
| 🟡 增量 | 加功能/加 API/加组件 | PRD 加验收项 → ARCH 加条目(如需) → 编码 → CHECKLIST |
| 🟢 修补 | 改文案/修 CSS/调提示 | 改代码 → 对照 PRD 异常场景确认文案 → 跑 gen_arch_stats |
| ⚪ 重构 | 搬家/改名/拆文件 | 改代码 → 更新 ARCH 文件路径 → 跑 gen_arch_stats |

---

## 模块防火墙

```
✅ 跨 App import Model（只读查询）
✅ 跨 App import api.py（复杂写操作）
❌ 跨 App import service/runner/consumer/state_machine（内部实现）
❌ 跨 App 直接 ORM 写（INSERT/UPDATE/DELETE 必须走 api.py）
❌ 前端直连数据库
❌ 仪表盘做写操作
❌ 错误提示暴露技术术语给用户
```

---

## 项目工具

| 工具 | 用途 |
|------|------|
| `python tools/gen_arch_stats.py` | 自动统计表/端点/Tool/步骤类型 |
| `python tools/gen_arch_stats.py --check-md` | 检测文档是否落后代码 |
| `python tools/gen_arch_stats.py --check-boundaries` | 检测跨模块 ORM 写违规 |
| `python run.py start / stop / status` | 启动/停止/检查平台 |

---

## .claude/ 配置

| 目录/文件 | 作用 |
|-----------|------|
| `.claude/agents/` | 子 Agent 定义（frontend-evaluator） |
| `.claude/skills/` | 专项流程（architecture-review / code-health-check / feature-analysis / functional-testing） |
| `.claude/hooks/` | 生命周期钩子（check-boundary.sh — 每次 Edit/Write 前检查边界；check-doc-drift.sh — 会话启动时检查文档漂移） |
| `.claude/memory/` | 教训沉淀（20 个文件），MEMORY.md 索引自动加载 |

---

## 关键约定

- API 响应统一 `{ok, data}` 或 `{ok, error}`
- JSON 字段 snake_case，前端变量 camelCase
- 数据库表前缀：`dp_` `el_` `cm_` `tr_` `rg_` `ai_` `wf_`
- 步骤类型唯一真相源：`models/step_types.py::StepType` 枚举（17 种）
- 设备状态：ONLINE / BUSY / OFFLINE（3 种，断连直接删记录）
- API Key 加密存储，前端脱敏展示，日志不输出 Key
