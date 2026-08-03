# Coding Conventions — Android-AutoTests

> **索引文件**。代码约束分散到各语言专属文件，本文只保留跨语言/跨层的约定。

---

## 代码约束

| 语言 | 文件 | 内容 |
|------|------|------|
| Python | `.claude/rules/python-code.md` | 命名 / 行数限制 / import / 类型注解 / api.py·views.py·models.py 规范 / 异常处理 / 响应格式 |
| 前端 | `.claude/rules/frontend.md` | 命名 / 行数限制 / 架构红线 / 数据加载三态 / CSS 层级 / Element Plus |

---

## 设备端测试步骤

> **获取完整步骤类型列表**：Read `models/step_types.py` → `class StepType(Enum)`。这是唯一真相源。步骤分发映射在 `apps/test_runner/executor.py` → `StepExecutor.execute()`。

## XPath 策略

> **获取 XPath 生成策略**：Read `apps/element_locator/service.py` → `gen_xpath_candidates()`。生成 8 种 XPath，按匹配数升序排列，优先选 count=1。

## 前端主题

全局统一 Doodle Craft 主题。规范文档 → `frontend/DESIGN_SYSTEM.md`

## JWT 鉴权

- Django + AgentScope 共享 `SECRET_KEY`
- `LoginView.vue` 是平台唯一登录入口
- `beforeEach` 守卫保护全部路由
- 前端 Axios 拦截器自动处理 401 刷新
