# AGENTS.md

## 行为准则

1. **用最少的代码解决问题。不接受过度设计。** 不添加需求之外的功能。用户说"加个筛选条件"，不要顺便"优化整个表格组件"

2. **只碰必须碰的。只清理自己造成的混乱。** 不要"顺手"改进相邻代码、注释、格式。diff 中每一行都应能追溯到用户的请求

3. **定义成功标准。循环验证直到达成。** 将指令转化为可验证的目标

4. **使用 openspec 技能来新增功能**

### 先看需求，再写代码

**先读文档，后写代码，不假设。不隐藏困惑。呈现权衡。** 需求不明确时， 先看 PRD 验收条件，列出可能的理解，让用户选择——不要默默挑一种执行

1. **功能变更前，先阅读 PRD，理解当期设计** 文件路径在`dev_docs/02-PRD需求` 
2. **编写代码前，先阅读ARCH， 理解模块职责** 文件路径在`dev_docs/03-设计与架构` 
3. **前端UI有变动时，先看文档，再看代码** 文件路径在`dev_docs/05-开发与测试` ，文件名举例：设计-仪表盘前端UI规范与checklist.md


### 报错先诊断，不动手

**看到错误日志、堆栈、浏览器 console 报错、服务异常时，禁止直接猜原因改代码。** 必须先在文字中完成以下三步：

1. **复述现象**："我看到了什么"
2. **列出可能原因**："可能的根因有 A / B / C"
3. **提出验证计划**："下一步查什么来确认"


## 工作偏好与经验教训

1. **宣布修复前必须浏览器 UI 端到端验证**——API/curl 通过 ≠ 修好；模拟用户点击走完整链路（≥2 次）才算完成
2. **命令/操作被拒 2 次即停**——不重复尝试第 3 次，直接告知用户手动执行
3. **方案/分析/流程文档额外输出 HTML**——Markdown 之外再生成 HTML，放 `tests/functional/{module}/reports/`，风格对齐 `html-report` skill
4. **每个任务结束输出执行摘要**——用了哪些 Skill/工具、走了什么流程
5. **项目负责人思维**——发现问题 → 归类根因 → 提 ≥2 个方案 → 让用户决策；不假装知道、不猜测、不确定就问
6. **创建了专用技能/子代理就必须用**——不手动绕过；表现不好就改进定义，而不是弃用


## 模块防火墙

> 详细规则 → `android-autotests-rules` skill（`references/api-conventions.md` / `references/architecture.md`）

```
✅ 跨 App import Model（只读查询）
✅ 跨 App import api.py（复杂写操作）
❌ 跨 App import service/runner/consumer/state_machine（内部实现）
❌ 跨 App 直接 ORM 写（INSERT/UPDATE/DELETE 必须走 api.py）
❌ 前端直连数据库
❌ 仪表盘做写操作
❌ 错误提示暴露技术术语给用户
```

## 架构红线

```
通信通道封闭集合（只这五条，禁止引入新协议 gRPC/MQTT/Kafka/RabbitMQ/GraphQL/WebRTC）：
① 前端 ↔ Django：HTTP REST + JWT   ② Django → 前端：WebSocket + JWT
③ 前端 → Django (AI)：SSE + JWT    ④ AgentScope → Django：进程内调用   ⑤ Django ↔ 设备：ADB

依赖方向：上层 import 下层；device_pool 是唯一底层；dashboard/ai_assistant 是聚合层
写操作铁律：任何写库（INSERT/UPDATE/DELETE）必须走目标模块 api.py，禁止直接 ORM 写
```

## 安全铁律

```
🔴 禁止硬编码密码/API Key/SECRET_KEY（用 os.environ.get()）
🔴 禁止认证绕过（JWT 无 token 必须 401；WebSocket connect 必须验 JWT）
🔴 禁止数据隔离缺失（列表/查询按 request.user_id 过滤）
🔴 写操作 catch 禁止静默吞错（前端 ElMessage.error / 后端 logging）
🔴 API 响应 api_key 必须脱敏（sk-***xxxx），日志不输出 Key
```

---

## 项目工具


| 工具                                                  | 用途                 |
| --------------------------------------------------- | ------------------ |
| `python tools/gen_arch_stats.py`                    | 自动统计表/端点/Tool/步骤类型 |
| `python tools/gen_arch_stats.py --check-md`         | 检测文档是否落后代码         |
| `python tools/gen_arch_stats.py --check-boundaries` | 检测跨模块 ORM 写违规      |
| `python run.py start / stop / status`               | 启动/停止/检查平台         |


---


## 关键约定

- API 响应统一 `{status, data}` 或 `{status, message}`
- JSON 字段 snake_case，前端变量 camelCase
- 数据库表前缀：`dp_` `el_` `cm_` `tr_` `rg_` `ai_` `wf_` `ev_` `di_`
- API Key 加密存储，前端脱敏展示，日志不输出 Key

