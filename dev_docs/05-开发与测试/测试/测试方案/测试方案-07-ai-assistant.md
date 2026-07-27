# 模块测试方案 — AI 智能助手

> 关联：`02-PRD需求/子PRD-06-ai-assistant.md` · 版本：v1.0 · 日期：2026-07-01

---

## 1. 测试范围

| 类型 | 内容 |
|------|------|
| 接口测试 | 18 个 AI REST 端点 + SSE 流 |
| AgentScope 测试 | 14 个 Tool 独立调用 + ReAct 推理链 |
| 前端测试 | 智能体列表 / 5 步向导 / SSE 聊天 / 动森主题 |
| 集成测试 | AI Tool → Django ORM 写入验证 |
| 降级测试 | AgentScope 不可用 → Django 阻塞模式 |

---

## 2. 智能体 CRUD 测试

| 编号 | 用例 | 预期 |
|:--:|------|------|
| AI-API-01 | 创建智能体（最低配） | POST /api/ai/agents/create → 200，name+model 必填 |
| AI-API-02 | 创建智能体（全配置） | 20+ 字段全部传入 → 200，字段持久化 |
| AI-API-03 | 获取智能体列表 | GET /api/ai/agents → 200，含 tool_count |
| AI-API-04 | 获取智能体详情 | GET /api/ai/agents/{id} → 200，含 tools 数组 |
| AI-API-05 | 更新智能体 | POST /api/ai/agents/{id}/update → 200 |
| AI-API-06 | 删除智能体 | POST /api/ai/agents/{id}/delete → 200，级联删 tools |

---

## 3. 对话与消息测试

| 编号 | 用例 | 预期 |
|:--:|------|------|
| AI-CONV-01 | 创建对话 | POST conversations/create → 200，返回 id |
| AI-CONV-02 | 获取对话列表 | GET conversations → 200，按 updated_at 倒序 |
| AI-CONV-03 | 获取消息 | GET conversations/{id}/messages → 200，空数组或历史 |
| AI-CONV-04 | 发送消息（降级） | POST /send → 200，返回 assistant 消息 |
| AI-CONV-05 | 保存消息 | POST /save-message → 200，写入 AIMessage |

---

## 4. AgentScope Tool 独立测试

> 不需要 AgentScope 服务运行 — 直接实例化 Tool 类调用 `call()`

| 编号 | Tool | 测试输入 | 预期输出包含 |
|:--:|------|------|------|
| AI-TOOL-01 | get_test_points | page_ids=[] | "No test points" 或元素列表 |
| AI-TOOL-02 | search_elements | query="Button" | "Results for 'Button'" |
| AI-TOOL-03 | save_test_case | case_id="test-001", title="测试", steps=[{type:"click",xpath:"//btn",description:"点按钮"}] | "saved successfully" |
| AI-TOOL-04 | get_test_case | case_id="test-001" | "Case: 测试" |
| AI-TOOL-05 | list_test_cases | case_ids=[] | 已启用的用例列表 |
| AI-TOOL-06 | get_online_devices | — | "Online devices" 或 "No online" |
| AI-TOOL-07 | acquire_device | serial="test" | "acquired" 或 "Cannot acquire" |
| AI-TOOL-08 | release_device | serial="test" | "released" 或 "release failed" |
| AI-TOOL-09 | run_test | run_id="run-001", serial="test", case_ids=["test-001"] | "completed" 或 "failed" |
| AI-TOOL-10 | get_run_results | run_id="run-001" | 执行结果列表 |
| AI-TOOL-11 | stop_run | run_id="run-001" | "stopped" 或 "not found" |
| AI-TOOL-12 | save_report | run_id="run-001", title="报告", file_path="/tmp/r.json" | "Report saved" |
| AI-TOOL-13 | list_reports | — | 报告列表 |
| AI-TOOL-14 | search_knowledge_base | query="click 步骤" | StepType 参考文档 |

---

## 5. AgentScope ReAct 推理链测试

> 需要 Django + Redis + AgentScope 全部运行

| 编号 | 场景 | 用户输入 | 预期 Tool 调用链 |
|:--:|------|------|------|
| AI-REACT-01 | 查询设备 | "查看在线设备" | get_online_devices → 返回设备列表 |
| AI-REACT-02 | 搜索元素 | "搜索登录按钮" | search_elements("登录按钮") → 返回匹配元素 |
| AI-REACT-03 | 生成用例 | "创建冒烟测试用例 test-002" | search_elements → save_test_case |
| AI-REACT-04 | 知识库检索 | "怎么创建用例步骤" | search_knowledge_base → 返回 StepType 文档 |
| AI-REACT-05 | 设备+执行 | "在设备 X 跑用例 test-001" | acquire_device → run_test → get_run_results |

---

## 6. SSE 流式输出测试

| 编号 | 用例 | 预期 |
|:--:|------|------|
| AI-SSE-01 | SSE 连接成功 | POST /agentscope/chat → 200，返回 session_id |
| AI-SSE-02 | 接收 TEXT_BLOCK_DELTA | 订阅 stream → 逐 token 到达 |
| AI-SSE-03 | AgentScope 不可用降级 | Redis 关闭 → 自动切到 /send 阻塞模式 |
| AI-SSE-04 | 消息回存 | SSE 完成 → AIMessage 表有新记录 |

---

## 7. 前端测试

| 编号 | 用例 | 操作 | 预期 |
|:--:|------|------|------|
| AI-UI-01 | 智能体列表 | 访问 /ai-assistant | AnimalCard 网格，含名称/标签/工具数 |
| AI-UI-02 | 新建智能体向导 | 点击"新建" → 5 步填写 | 步骤切换正常，保存后列表刷新 |
| AI-UI-03 | 模型切换 | Step2 选择不同 provider | 模型下拉列表联动更新 |
| AI-UI-04 | MCP 服务器 | Step4 添加 stdio/SSE/HTTP | 配置 JSON 正确生成 |
| AI-UI-05 | 对话侧边栏 | /ai-assistant/chat/{id} | 对话列表 + 切换 + 新建 |
| AI-UI-06 | 流式输出 | 输入消息 → 回车 | 文字逐字出现 |
| AI-UI-07 | 动森主题 | 检查 AI 模块各页面 | AnimalButton/Card/Switch/Cursor/Footer 生效 |
| AI-UI-08 | 动森不污染业务 | 访问 /devices /elements 等 | Element Plus 蓝色，非动森暖色 |

---

## 8. 动森主题隔离测试

| 编号 | 检查项 | 预期 |
|:--:|------|------|
| AI-THEME-01 | LoginView | AnimalCard + AnimalInput + AnimalButton + Title |
| AI-THEME-02 | 智能体列表 | AnimalCard 网格 + AnimalButton |
| AI-THEME-03 | AgentDetail | AnimalSwitch + AnimalDivider + AnimalButton |
| AI-THEME-04 | ChatView | AnimalButton 发送按钮 |
| AI-THEME-05 | App.vue | Cursor 自定义光标 + Footer type="tree" |
| AI-THEME-06 | 业务模块不受影响 | /devices 使用 el-button 蓝色直角 |

---

## 9. Agent Team 测试

| 编号 | 用例 | 预期 |
|:--:|------|------|
| AI-TEAM-01 | 模板加载 | SUB_AGENT_TEMPLATES 5 个 | type 分别为 inspector/case-writer/operator/executor/writer |
| AI-TEAM-02 | Leader prompt | build_leader_system_prompt() | 包含"Test Automation Lead" |
| AI-TEAM-03 | 编队调度 | Leader 接复杂任务 | 日志可见 Worker spawn |

---

## 10. 知识库测试

| 编号 | 用例 | 预期 |
|:--:|------|------|
| AI-KB-01 | 文档加载 | load_all_documents() | ≥30 篇 |
| AI-KB-02 | 向量检索 | search("click 步骤类型") | 返回 StepType 参考文档 |
| AI-KB-03 | 初始化脚本 | python init_kb.py | 无错误 |
| AI-KB-04 | 重置脚本 | python init_kb.py --reset | 清空后重建 |

---

## 11. 智能体 CRUD 数据库同步测试（2026-07-03 补充）

> **背景**：前端多次出现删除/新增后数据与数据库不一致的问题，根因是 `catch (_) {}` 静默吞错 + Vite 500 模块加载失败。
> 此测试套件从 API、数据库、前端三层验证数据同步。

### 测试环境

| 项目 | 值 |
|------|------|
| 后端 | Django :8765 (MySQL) |
| 前端 | Vite :5173 |
| 测试工具 | curl + Python requests + MySQL 直查 |
| 测试日期 | 2026-07-03 |

### 11.1 删除同步测试

| 编号 | 用例 | 步骤 | 预期 | 实际 |
|:--:|------|------|------|:--:|
| AI-DEL-01 | API 删除 → 列表验证 | 1. POST /delete 2. GET /agents | 列表中不包含已删除 Agent | ✅ |
| AI-DEL-02 | API 删除 → 数据库直查 | 1. POST /delete 2. MySQL SELECT | DB 中不存在已删除记录 | ✅ |
| AI-DEL-03 | 前端删除 → API 验证 | 1. 前端点删除 2. curl GET /agents | API 返回列表不包含 | ✅ |
| AI-DEL-04 | 前端删除 → 数据库直查 | 1. 前端点删除 2. MySQL SELECT | DB 物理删除（非软删除） | ✅ |
| AI-DEL-05 | 删除不存在的 Agent | POST /delete id=9999 | 返回 ok=True（filter 无匹配，幂等） | ✅ |
| AI-DEL-06 | 级联删除 | 删除含 3 个 Tool 的 Agent | Agent + 3 条 Tool 全部删除 | 待测 |
| AI-DEL-07 | 删除含对话的 Agent | 删除含 2 条 Conversation 的 Agent | Agent + 对话 + 消息级联删除 | 待测 |
| AI-DEL-08 | 同一 Agent 重复删除 | POST /delete 两次 | 两次都返回 ok=True（幂等） | ✅ |

### 11.2 新增同步测试

| 编号 | 用例 | 步骤 | 预期 | 实际 |
|:--:|------|------|------|:--:|
| AI-CREATE-01 | API 新增 → 列表验证 | 1. POST /create 2. GET /agents | 列表包含新 Agent | ✅ |
| AI-CREATE-02 | API 新增 → 数据库直查 | 1. POST /create 2. MySQL SELECT | DB 中存在完整字段 | ✅ |
| AI-CREATE-03 | 前端新增 → API 验证 | 1. 前端创建 2. curl GET /agents | API 返回列表包含 | 待前端测 |
| AI-CREATE-04 | 前端新增 → 数据库直查 | 1. 前端创建 2. MySQL SELECT | DB 中存在，api_key 已加密 | 待前端测 |
| AI-CREATE-05 | 新增后 api_key 加密 | POST /create 传 api_key | DB 中不以 sk- 开头（Fernet 密文） | ✅ |
| AI-CREATE-06 | 新增后 key_revealed 初始值 | POST /create | DB 中 key_revealed=False | ✅ |

### 11.3 完整闭环测试

| 编号 | 用例 | 步骤 | 预期 | 实际 |
|:--:|------|------|------|:--:|
| AI-CRUD-01 | 创建→列表→删除→列表→DB | 5 步全链路 | 最终数据一致 | ✅ |
| AI-CRUD-02 | 连续创建 2 个→删 1 个→保留 1 个 | 批量操作 | 删的消失，保留的存在 | ✅ |
| AI-CRUD-03 | 创建→删除→重创同 name | 3 步 | 新 id ≠ 旧 id | ✅ |
| AI-CRUD-04 | 数量守恒 | N 个→创建→删除→仍为 N 个 | 前后数量一致 | ✅ |

### 11.4 前端静默吞错防护测试

| 编号 | 用例 | 步骤 | 预期 | 实际 |
|:--:|------|------|------|:--:|
| AI-ERR-01 | 删除 API 500 → 前端表现 | 1. 模拟 API 返回 500 2. 前端点删除 | ElMessage.error 提示 + 列表不变化 | 待前端测 |
| AI-ERR-02 | 删除网络断开 → 前端表现 | 1. 断开网络 2. 前端点删除 | ElMessage.error 提示 | 待前端测 |
| AI-ERR-03 | 新增 API 500 → 前端表现 | 1. 模拟 API 返回 500 2. 前端点创建 | ElMessage.error 提示 + 列表不增加 | 待前端测 |
| AI-ERR-04 | 列表加载失败 → 前端表现 | 1. 模拟 GET /agents 500 | ElMessage.error + 列表为空（非残留旧数据） | 待前端测 |

### 11.5 自动化测试脚本

```bash
# 完整 CRUD 同步测试（API + DB 双重验证）
cd D:/Kahoku/Android-AutoTests && python -c "
import os, json, requests
BASE = 'http://localhost:8765'
login = requests.post(f'{BASE}/api/ai/auth/login',
    json={'username':'admin','password':'admin123'})
TOKEN = login.json()['access_token']
H = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}

# Snapshot
before = len(requests.get(f'{BASE}/api/ai/agents', headers=H).json()['agents'])

# Create
r = requests.post(f'{BASE}/api/ai/agents/create', headers=H,
    json={'name':'CRUD-Test','model_provider':'custom','model_name':'test'})
new_id = r.json()['id']
assert r.json()['ok']

# Verify in list
agents = requests.get(f'{BASE}/api/ai/agents', headers=H).json()['agents']
assert any(a['id'] == new_id for a in agents), 'Not in list'

# Verify in DB
os.environ.update(DB_ENGINE='mysql', DB_NAME='android_autotests',
    DB_USER='root', DB_PASSWORD='autotests2026', DB_HOST='127.0.0.1', DB_PORT='3306')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()
from apps.ai_assistant.models import AIAgent
assert AIAgent.objects.filter(id=new_id).exists(), 'Not in DB'

# Delete
assert requests.post(f'{BASE}/api/ai/agents/{new_id}/delete', headers=H).json()['ok']

# Verify gone
agents = requests.get(f'{BASE}/api/ai/agents', headers=H).json()['agents']
assert not any(a['id'] == new_id for a in agents), 'Still in list'
assert not AIAgent.objects.filter(id=new_id).exists(), 'Still in DB'

# Count check
after = len(agents)
assert before == after, f'Count mismatch: {before} vs {after}'
print(f'ALL PASSED — before={before} after={after}')
"
```

### 11.6 测试结论

| 结论 | 说明 |
|------|------|
| **API → DB 同步** | ✅ 创建和删除操作正确同步到 MySQL |
| **列表反射** | ✅ GET /agents 实时反映增删变化 |
| **api_key 加密** | ✅ 新增时 Fernet 加密存储 |
| **幂等性** | ✅ 删除不存在的 Agent 不报错 |
| **前端同步** | ⚠️ 依赖前端修复后的 catch 处理（AI-ERR-01~04 待测） |

### 11.7 关联规则

| 规则文件 | 相关章节 |
|---------|---------|
| `frontend.md` | 代码变更后必检、数据来源铁律、写操作静默吞错检查 |
| `security.md` | API Key 生命周期安全规则、数据库存储加密类 |
| `api-conventions.md` | ai-assistant 端点完整清单 |
