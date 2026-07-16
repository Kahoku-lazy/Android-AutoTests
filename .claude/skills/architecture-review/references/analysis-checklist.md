# Architecture Analysis Checklist

架构审查五维检查清单，Phase 2 执行时逐项对照。

## 一、高内聚检查

| # | 检查项 | 命令/方法 | 判定标准 |
|---|--------|---------|---------|
| 1 | 各 App models.py 只定义本模块表 | `grep "class.*models.Model" apps/{app}/models.py` | 无跨模块表定义 |
| 2 | views.py 不包含其他模块的业务逻辑 | 阅读 `apps/{app}/views.py` | 只处理本模块资源 |
| 3 | 没有 A 模块的代码文件散落在 B 模块目录 | `find apps/{app} -name "*.py"` | 文件名与目录名语义一致 |
| 4 | 前端模块有对应的后端 App | 对照 `frontend/src/modules/` 与 `apps/` | 一一对应 |

## 二、低耦合检查

| # | 检查项 | 命令/方法 | 判定标准 |
|---|--------|---------|---------|
| 1 | 跨模块写操作走 api.py | `grep -rn "from apps\..*\.views import" .` | 无命中 |
| 2 | 跨模块读操作不走 service | `grep -rn "from apps\..*\.service import" .` | 无命中 |
| 3 | 无循环依赖 | 绘制依赖图，检查闭环 | 严格单向 DAG |
| 4 | 前端模块间不通过 event-bus 隐式耦合 | `grep -rn "bus.emit\|event-bus" frontend/src/` | 记录所有 event |

## 三、分层合理性检查

| # | 检查项 | 检查方法 | 判定标准 |
|---|--------|---------|---------|
| 1 | 底层模块无业务依赖 | 检查 device_pool, report_generator 的 import | 不 import 其他 App |
| 2 | 聚合模块在最上层 | 检查 ai_assistant 的 import | 依赖所有（聚合层） |
| 3 | 依赖方向单向向下 | 所有跨模块 import 方向一致 | A→B→C，无 C→A |
| 4 | 层级在 3-4 层 | 统计 L1~L4 | 不过深不过浅 |

## 四、安全检查

| # | 检查项 | 命令/方法 | 判定标准 |
|---|--------|---------|---------|
| 1 | WebSocket connect() 有 JWT 验证 | `grep -A5 "def connect" apps/*/consumers.py` | 含 token 验证 |
| 2 | 无硬编码密码/Key | `grep -rn "password\s*=\s*'[^']*'" apps/` | 无命中 |
| 3 | api_key 加密存储 | `SELECT api_key FROM ai_agents LIMIT 1` | 不以 sk- 开头 |
| 4 | 前端不直连后端端口 | `grep -rn ":8765\|:8000" frontend/src/` | 仅 ws-url.js |

## 五、一致性检查

| # | 检查项 | 命令/方法 | 判定标准 |
|---|--------|---------|---------|
| 1 | 所有 App 有 api.py/serializers.py/permissions.py | `ls apps/{app}/*.py` | 全部存在 |
| 2 | 所有前端模块有 api.js/routes.js | `ls frontend/src/modules/{mod}/*.js` | 全部存在 |
| 3 | 数据库表前缀一致 | `SHOW TABLES` | 6 组前缀 |
| 4 | URL 前缀与模块名一致 | `grep "path" apps/{app}/urls.py` | kebab-case |

## 评分

每项合格得 1 分，满分 20 分：

| 分数 | 评级 | 建议 |
|------|:--:|------|
| 18-20 | 🟢 优秀 | 保持 |
| 14-17 | 🟡 良好 | 补齐 P1 项 |
| 8-13 | 🟠 需改进 | 先修 P0/P1 |
| <8 | 🔴 严重 | 立即重构 |
