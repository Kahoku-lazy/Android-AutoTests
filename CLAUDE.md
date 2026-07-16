# CLAUDE.md — Android-AutoTests

> 我是这个项目的 AI 开发工程师。本文档是每次对话的入口指令。

---

## 项目身份

Android-AutoTests — AI 驱动的 Android UI 自动化测试平台。
- **8 模块**：设备管理 / 元素定位 / 用例管理 / 执行引擎 / 测试报告 / AI 助手 / 工作流工作台 / 仪表盘
- **三层架构**：Vue 3 :5173 + Django :8765 + AgentScope :8000
- **17 种步骤类型**，22 张业务表，106 个 API 端点，24 个 AgentScope Tool

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
