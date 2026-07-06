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

## 设备端测试步骤 (14 种)

命名采用 `snake_case`，动词在前，语义直观。

### 点击操作

| 步骤 | 功能 |
|------|------|
| `click` | 点击匹配的单个 UI 元素 |
| `click_indexed` | 点击 XPath 匹配列表中的第 N 个元素（索引从 0 开始） |
| `retry_click` | 带重试的点击，元素未出现时自动等待并重试，适用于加载延迟场景 |

### 等待操作

| 步骤 | 功能 |
|------|------|
| `wait` | 等待指定元素出现，超时可配，常用于页面跳转后确认加载完成 |
| `wait_disappear` | 等待指定元素从屏幕上消失，用于 loading 遮罩、过渡动画等 |
| `wait_either` | 等待两个候选元素之一出现，用于不确定跳转结果的分支场景 |
| `wait_toast` | 等待 Toast 弹出并提取消息文本，用于校验操作反馈 |

### 验证操作

| 步骤 | 功能 |
|------|------|
| `verify_text` | 校验指定元素的 text 内容是否匹配期望值，用于断言页面状态 |
| `poll_text` | 轮询元素文本并在变化时返回，用于监控动态更新的 UI 文本 |

### 应用控制

| 步骤 | 功能 |
|------|------|
| `start_app` | 启动目标 App（通过 package name） |
| `kill_app` | 强制停止目标 App |
| `restart_app` | 先 kill 再 start，用于恢复 App 初始状态 |

### 工具步骤

| 步骤 | 功能 |
|------|------|
| `sleep` | 固定时长暂停（秒），用于等待非 UI 操作的完成 |
| `log` | 在测试报告中插入一条文本日志，不执行任何设备操作 |

## XPath 策略

`gen_xpath_candidates()` 生成 8 种 XPath，按匹配数升序排列，优先选 count=1。

## 前端主题隔离

- **业务模块**：Element Plus 蓝白风格（默认主题）
- **AI 助手模块**：animal-island-vue（暖木色/大圆角），CSS 变量覆盖在 `animal-theme.css`

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
