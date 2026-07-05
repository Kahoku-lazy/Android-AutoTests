# AI Assistant Test Cases

> 对应脚本: `scripts/run_ai_tests.py`
> 用例设计规范: `references/test-case-design.md`

## 数据库验证层

### AI-DB-01: 删除后数据库物理删除

**层次**: DB
**脚本函数**: `test_ai_db_01_delete_sync()`

**步骤**:
1. 获取当前 Agent 数量 N
2. 临时创建 Agent
3. 调用 DELETE API
4. MySQL 直查确认记录不存在
5. 确认 Agent 总数恢复为 N

**预期**: 物理删除，总数守恒

### AI-DB-02: 新增后 api_key 加密存储

**层次**: DB
**脚本函数**: `test_ai_db_02_key_encrypted()`

**步骤**:
1. 创建 Agent（传入 api_key="sk-test-plaintext"）
2. MySQL 直查 `ai_agents.api_key` 字段
3. 确认值不以 "sk-" 开头

**预期**: api_key 为 Fernet 密文（非明文 sk- 开头）

### AI-DB-03: key_revealed 初始值为 False

**层次**: DB
**脚本函数**: `test_ai_db_03_revealed_default()`

**步骤**:
1. 创建 Agent
2. MySQL 直查 `key_revealed` 字段

**预期**: key_revealed = 0 (False)

### AI-DB-04: 级联删除 Tools

**层次**: DB
**脚本函数**: `test_ai_db_04_cascade_tools()`

**步骤**:
1. 创建 Agent（含 2 个 Tool）
2. 删除 Agent
3. MySQL 直查 ai_tools 确认关联记录已删除

**预期**: Agent 和关联 Tool 全部删除

## API 接口测试层

### AI-API-01: 创建 Agent（最低配置）

**层次**: API
**脚本函数**: `test_ai_api_01_create_minimal()`

**步骤**:
1. POST /api/ai/agents/create {"name":"test","model_provider":"custom","model_name":"test"}
2. 验证 HTTP 200 + ok=True

**预期**: 创建成功，返回 id

### AI-API-02: 获取 Agent 列表不含 api_key

**层次**: API
**脚本函数**: `test_ai_api_02_list_no_key()`

**步骤**:
1. GET /api/ai/agents
2. 验证响应中每个 agent 不含 "api_key" 字段

**预期**: 列表中无敏感字段

### AI-API-03: 获取 Agent 详情 api_key 已脱敏

**层次**: API
**脚本函数**: `test_ai_api_03_detail_masked()`

**步骤**:
1. GET /api/ai/agents/1
2. 验证 api_key 字段包含 "***"

**预期**: 脱敏值 sk-***xxxx

### AI-API-04: 更新 Agent 掩码检测

**层次**: API
**脚本函数**: `test_ai_api_04_update_mask_detect()`

**步骤**:
1. POST /api/ai/agents/1/update {"api_key":"sk-***f25f"}
2. 验证 DB 中 api_key 未改变

**预期**: "***" 掩码被跳过，原值保留

### AI-API-05: 删除不存在的 Agent

**层次**: API
**脚本函数**: `test_ai_api_05_delete_nonexistent()`

**步骤**:
1. POST /api/ai/agents/99999/delete
2. 验证 HTTP 200 + ok=True

**预期**: 幂等返回 ok（filter 无匹配不抛异常）

## 前端验证层

### AI-UI-01: 模块正常加载

**层次**: UI
**脚本函数**: `test_ai_ui_01_module_load()`

**步骤**:
1. curl http://localhost:5173/src/modules/ai-assistant/index.vue
2. 验证 HTTP 200

**预期**: 模块编译成功，无 Vite 500

### AI-UI-02: 列表数据来自 API

**层次**: UI
**脚本函数**: `test_ai_ui_02_list_from_api()`

**步骤**:
1. GET /api/ai/agents 获取 API 数据
2. 验证 前端模块加载(200) + API 返回数据一致

**预期**: 前端模块无语法错误，数据与 API 同步

## 错误防护层

### AI-ERR-01: 删除 API 500 → 前端应报错

**层次**: ERR
**脚本函数**: `test_ai_err_01_delete_fail_visible()`

**步骤**:
1. 检查前端 index.vue 中 deleteAgent 函数
2. 验证 catch 块包含 ElMessage.error

**预期**: 删除失败时前端有用户可见的错误提示

### AI-ERR-02: 列表加载失败 → 前端应报错

**层次**: ERR
**脚本函数**: `test_ai_err_02_load_fail_visible()`

**步骤**:
1. 检查前端 index.vue 中 loadAgents 函数
2. 验证 catch 块包含 ElMessage.error

**预期**: 加载失败时前端有用户可见的错误提示
