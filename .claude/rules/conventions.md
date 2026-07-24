# Coding Conventions — Android-AutoTests

## 命名规范

| 上下文 | 规范 | 示例 |
|--------|------|------|
| 后端 Python | `snake_case` | `test_runner`, `get_device()` |
| 前端 JS/Vue | `camelCase` | `apiClient`, `getDevices()` |
| Vue 组件文件 | `PascalCase.vue` | `AgentDetail.vue`, `AppSidebar.vue` |
| Vue 组件模板 | `kebab-case` | `<device-pool>`, `<case-manager>` |
| API URL | `kebab-case` | `/api/device-pool/`, `/api/test-runner/` |
| JSON 字段 | `snake_case` | `{"test_case_id": 1, "run_status": "OK"}` |
| 数据库表 | `{prefix}_snake_case` | `dp_devices`, `cm_test_cases` |
| Model 类 | `PascalCase` | `Device`, `TestCase`, `TestRun` |
| CSS class | `kebab-case` | `.device-card`, `.test-result` |

## 设备端测试步骤

> **获取完整步骤类型列表**：Read `models/step_types.py` → `class StepType(Enum)`。这是唯一真相源。步骤分发映射在 `apps/test_runner/executor.py` → `StepExecutor.execute()`。

## XPath 策略

> **获取 XPath 生成策略**：Read `apps/element_locator/service.py` → `gen_xpath_candidates()`。生成 8 种 XPath，按匹配数升序排列，优先选 count=1。

## 前端主题

- **全局主题**：Crayon Doodle 手绘卡通风格（`tokens.css`），粗线条 3px 墨色边框、不对称圆角、涂鸦纹理、卡通字体
- **AI 助手模块**：`.ai-workbench` 绿色调主题变体（`tokens.css`），独立 accent 色板
- **色值从 `tokens.css` 取**，禁止组件内硬编码颜色

## JWT 鉴权

- Django + AgentScope 共享 `SECRET_KEY`
- `LoginView.vue` 是平台唯一登录入口
- `beforeEach` 守卫保护全部路由
- 前端 Axios 拦截器自动处理 401 刷新

## 文件行数限制

单文件超过上限必须拆分，禁止继续堆代码。

| 文件类型 | 上限 | 超限处理 |
|------|:--:|------|
| `.vue` 组件 | 500 行 | 拆出 composables / 子组件 |
| `.py` 模块 | 400 行 | 拆出独立模块 |
| 测试入口 `run_tests.py` | 300 行 | 拆出 `{layer}_tests.py` + `helpers.py` |
| 测试层文件 | 300 行 | 拆更细的测试分组文件 |

**自查命令**：
```bash
find . -name "*.py" -o -name "*.vue" | xargs wc -l | sort -rn | head -20
```
