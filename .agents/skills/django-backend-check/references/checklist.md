# Django 后端校验 — 完整检查表

> 由 `SKILL.md` 按需加载。判罚争议以 [calibration.md](calibration.md) 为准。

## 一、框架与工具层（P0）

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | system check | `python manage.py check` | 0 issues；见 calibration §3 | `staticfiles.W004` 未处理 |
| 2 | migration 同步 | `makemigrations --check` | 无缺失；未改 Model→N/A | 改了 Field 忘 migration |
| 3 | ruff lint | `ruff check <scope>` | 0 error | 裸 except、未用 import |
| 4 | ruff format | `ruff format --check <scope>` | 通过 | 与 CI 路径不一致漏扫 |
| 5 | 边界 | `gen_arch_stats.py --check-boundaries` | 无新增违规；纯本模块→可 N/A 但建议跑 | 跨 App `service` import |

## 二、风格与写法层（P1）

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | ruff 规则族 | I/F401/F403/E722/T201/Q | 对齐 `ruff.toml` | `print()` 留业务路径 |
| 2 | 命名 | 读公开符号 | snake_case / PascalCase / JSON snake_case | JSON 用 camelCase |
| 3 | 类型注解 | api/service 签名 | 有注解与 docstring | 裸 `def f(x):` |
| 4 | 文件行数 | `wc -l` / 目测 | 未破阶梯；破了有拆分 | views 上千行继续堆 |
| 5 | 函数内 import | `rg "^\s+from |^\s+import "` | 无（循环依赖先修边界） | 为躲循环塞局部 import |

## 三、架构 / 写库层（P0）

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | 职责分层 | 读 views/api | views 薄；api 无 JsonResponse/Model 返回 | view 里 200 行业务 |
| 2 | 写库收敛 | `rg "\.objects\.(create\|update\|filter)|\.save\(|\.delete\("` | 写在 api.py（或 admin） | views 直接 `Model.objects.create` |
| 3 | api 契约 | 读 `__all__` 与签名 | 白名单；参数简单类型；不收 request | `def f(request):` |
| 4 | 防火墙 #1 | `rg "from apps\.\w+\.(service\|runner\|state_machine)"` | 无跨 App 内部 import | `from apps.test_runner.service import …` |
| 5 | 防火墙 #2 | 跨 App Model + 写操作同文件 | 写外表必须走对方 api | 本模块改 `dp_` 表却不在 device_pool.api |
| 6 | dashboard | 读 `apps/dashboard` | 无写操作 | dashboard 里 save |
| 7 | db_table | 新/改 Model | 前缀 + 显式 `db_table` | 默认 app_label 表名 |

## 四、接口 / 协议层（P0）

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | 路由 | urls + config/urls | include + path 齐全 | 只改 views 未注册 |
| 2 | 信封 | 所有返回点 | `{status, data\|message}` + HTTP code | 裸 dict / 只 message 无 status |
| 3 | 字段契约 | Serializer↔Model↔前端 | 名与可选性一致 | Model 改名 Serializer 未改 |
| 4 | 鉴权 | 中间件/公开列表 | `user_id`；公开路径正确 | 误加公开或漏鉴权 |
| 5 | 错误文案 | catch / status false | 友好中文；禁技术词 | 返回 traceback 字符串 |
| 6 | WS | consumers + gateway/routing | 已注册；type 与前端对齐 | 漏中央路由 |

## 五、错误处理与副作用

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | 写操作吞错 | `rg "except.*:\s*(pass\|\\.\\.)"` | 有日志或 message；**否则 🔴** | `except: pass` 在 create 后 |
| 2 | 读失败路径 | list/get | 失败可区分 / 空态 | 异常当空列表且 status true |
| 3 | 阻塞/超时 | async/WS/外部调用 | 有超时或线程边界 | 在 consumer 里同步长阻塞 |
| 4 | Tool | Tool 实现 | 只调 api.py | Tool 直接 ORM 写 |

## 六、测试层

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | unit | `pytest -m unit` 相关 | 通过或 N/A+理由 | 纯逻辑无测且关单 |
| 2 | integration/api | `pytest -m "integration or api"` | 改写库/HTTP 时通过 | 只 check 不测接口 |
| 3 | 同改测试 | diff 调用方/测试 | 签名变更测试已更新 | api 改参测试仍旧签名 |

## 七、契约对照执行细则

见 SKILL.md §七；输出必须含三张表（路径 / 信封 / 字段），不适用整节标 N/A 并说明「未改 HTTP」。

## 常用扫描命令

见 [calibration.md](calibration.md) §7；另可：

```bash
rg -n "JsonResponse|Response\(" apps/<app>/
rg -n "__all__" apps/<app>/api.py
rg -n "db_table" apps/<app>/models*.py
rg -n "from apps\.\w+\.(service|state_machine|runner)" apps/
rg -n "except\s*(\(|:)|except\s+\w+.*:\s*pass" apps/<app>/
```
