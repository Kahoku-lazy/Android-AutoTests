---
name: django-backend-check
description: |
  Django 后端代码校验门禁 — 带统一判罚量规：system check、ruff、迁移、写库收敛/防火墙、响应信封、api.py 契约、静默吞错、文件行数。强制逐项记录防同 skill 结果漂移。
  Keywords: Django校验, 后端检查, 后端自检, manage.py check, ruff, 防火墙, api.py, 接口契约, backend checklist, 关单门禁
  Trigger: 用户表达"校验后端/检查 Django/后端自检/后端门禁/apps 关单检查"，或改完 apps/ / views / api.py / models / serializers / consumers 后要求确认是否可关单时。
---

# Django Backend Check — 后端代码校验门禁

**目的**: 改完 `apps/` / Django 后端后自检。`manage.py check` + ruff 通过 ≠ 完成。

**防漂移（必读）**: 同一 skill 两次结果不得凭感觉升降严重度 → 判罚必须以 [references/calibration.md](references/calibration.md) 为准。

**关联**:
- `apps/CLAUDE.md` / `dev_docs/项目笔记/后端claude笔记.md`
- `apps/自测与检测指令.md`（命令速查）
- `.claude/rules/backend.md` / `api-conventions.md` / `python-code.md` / `database.md`
- 检查细表 → [references/checklist.md](references/checklist.md)
- **量规/例外/强制输出** → [references/calibration.md](references/calibration.md)

**分层口诀**：`urls` 路径对不对 → `views/serializers` 信封与校验对不对 → `api.py` 写库对不对 → `models` 迁移与表前缀对不对。

## 工作流

```
1. 定范围 + 声明验证方式（静态 | 静态+pytest | 静态+curl/手工）
2. 先跑 calibration §7 强制命令，再读 urls → views → api → models 链
3. 按清单逐项给 ✅/⚠️/❌/N/A（不得只报缺陷）
4. 严重度只准查 calibration §2 表
5. 输出三块：缺陷表 + 逐项记录 + 结论
```

**硬性禁止**:
- 未跑 §7 强制命令却对一.1～一.4 / 二.x 下 ✅
- 把跨 App ORM 写、静默吞错写库、信封错误标成 🟡
- 只输出缺陷表、省略逐项扫描记录
- 把「仅静态体检」报告当作可关单依据却不在结论标明

## 最短路径

```
只改纯函数 / util           → 二.1～二.3 + 六.unit
改 models / migration       → 一.2 + 三全部 + 六.integration
改 api.py 写路径            → 三.2～三.5 + 四.1～四.3 + 五.1
改 views / serializers /urls→ 四全部 + 五全部 + 一.1
改 consumers / WS           → 四.6 + 五.3 + gateway/routing 注册
改跨模块调用                → 三.4～三.5 + §7 边界扫描（每次）
任意改动                    → 一全部 + 二全部（每次必做）
```

## 检查清单（摘要）

细则 → checklist.md；争议口径 → calibration.md。

### 一、框架与工具层（P0，每次必做）

| # | 检查项 | 通过标准（要点） |
|---|--------|------------------|
| 1 | `manage.py check` | 0 issues（W004 等见 calibration §3） |
| 2 | `makemigrations --check` | 无漏 migration（未改 Model → N/A） |
| 3 | `ruff check` | 目标路径 0 error |
| 4 | `ruff format --check` | 格式通过 |
| 5 | 边界扫描 | `--check-boundaries` 无新增违规（涉及跨模块时必做） |

### 二、风格与写法层（P1）

| # | 检查项 | 通过标准（要点） |
|---|--------|------------------|
| 1 | Import / 裸 except / print | 对齐 `ruff.toml` + python-code §3/§8/§11 |
| 2 | 命名 | snake_case 函数；PascalCase 类；JSON snake_case |
| 3 | 类型注解 | 公开 api/service 函数有注解 |
| 4 | 文件行数 | 未超阶梯；超限须拆分计划（calibration §4） |
| 5 | 函数内 import | 禁止（循环依赖须先修边界） |

### 三、架构 / 写库层（P0）

| # | 检查项 | 通过标准（要点） |
|---|--------|------------------|
| 1 | 文件职责 | views 不分发重逻辑；api 不返回 JsonResponse/Model |
| 2 | 写库收敛 | INSERT/UPDATE/DELETE 只在 api（或 Admin） |
| 3 | api `__all__` | 跨模块导出在白名单；参数简单类型，不收 request |
| 4 | 防火墙 #1 | 无跨 App import service/runner/consumer/state_machine |
| 5 | 防火墙 #2 | 无跨 App ORM 写外表 |
| 6 | dashboard | 无写操作 |
| 7 | 表前缀 / db_table | 前缀正确且显式 `db_table` |

### 四、接口 / 协议层（P0，改 HTTP 时必做）

| # | 检查项 | 通过标准（要点） |
|---|--------|------------------|
| 1 | 路由注册 | `urls.py` + `config/urls.py` include 齐全 |
| 2 | 响应信封 | `{status, data\|message}`；错误有 HTTP 状态码；**已登记特例除外**（test_runner `/runner/*`、report_generator `/reports/*`、workflow legacy 平铺，唯一登记 `apps/CLAUDE.md` §1.3，禁止新增） |
| 3 | Serializer↔Model↔前端 | 字段名/可选性一致（对照契约） |
| 4 | 鉴权上下文 | 用 `request.user_id`；公开路径未误伤 |
| 5 | 错误文案 | 用户可见；**禁技术词**（calibration §5） |
| 6 | WS 注册 | Consumer 在 `gateway/routing.py`；事件 type 双边对齐 |

### 五、错误处理与副作用（P0/P1）

| # | 检查项 | 通过标准（要点） |
|---|--------|------------------|
| 1 | 写操作吞错 | 禁止空 except / pass；须日志或返回 message → 否则 **🔴** |
| 2 | 读操作失败 | 有明确失败路径或空态，不假成功 |
| 3 | 外部 I/O | 超时/失败可感知；不无限阻塞事件循环（WS/async） |
| 4 | Tool 写库 | AgentScope Tool 只调 api.py |

### 六、测试层（关单相关）

| # | 检查项 | 通过标准（要点） |
|---|--------|------------------|
| 1 | unit | 纯逻辑有覆盖或说明 N/A 理由 |
| 2 | integration / api | 改写库或 HTTP 时跑过相关 marker |
| 3 | 签名同改 | api/Serializer 变更带动调用方与测试 |

> 未跑 pytest：六.x 不得 ✅（最多 ⚠️）；「关单」要求时相关 marker 必须跑过（calibration §1）。

### 七、契约对照（改接口每次必做）

> 本项是四.2 / 四.3 的**执行细则**。不得只写「已确认」。

**7.1 路径对照表**

| 前端/调用方 | HTTP 方法 | 后端 `urls.py` | 一致 |
|------------|:---------:|----------------|:----:|
| … | GET/POST | `apps/…/urls.py` → `path(...)` | ✅/❌ |

**7.2 信封对照表**

| 视图方式 | 识别 | 期望格式 |
|---------|------|----------|
| DRF `Response` | APIView / ViewSet | `{status, data}`（经统一 renderer 则按其实现） |
| `JsonResponse` | `@csrf_exempt` 手工返回 | 必须仍是 `{status, data\|message}` |
| `JsonResponse` | 已登记特例（`/runner/*`、`/reports/*`、workflow legacy） | 平铺 `{status, ...}`；对照 `apps/CLAUDE.md` §1.3 与对应 App `CLAUDE.md` 契约段，不得新增同类特例 |

**7.3 字段对照表**

| 接口 | 后端字段 | 前端/调用方字段 | 一致 |
|-----|---------|----------------|:----:|
| … | snake_case | … | ✅/❌ |

## 输出格式（强制三块）

```markdown
# Django 后端校验 — {范围}

验证方式: 静态扫描 | 静态+pytest | 静态+curl/手工
强制命令: 已执行 calibration §7（是/否）
命令摘要: check=… | makemigrations=… | ruff=… | boundaries=… | pytest=…

## 缺陷汇总
| # | 严重度 | 层级 | 文件 | 检查项 | 现象 | 建议 |
|---|--------|------|------|--------|------|------|
| … | 🔴/🟠/🟡 | … | path:Lxx | … | … | … |

## 逐项扫描记录
### 一、框架与工具层
| # | 结果 | 备注 |
| 1 | ✅/⚠️/❌/N/A | … |
（二～七同理，不适用标 N/A）

## 结论
- 通过 / 有条件通过 / 不通过
- 验证方式是否满足关单：是/否
- 阻塞关单项：…
```

## 与其它 skill 分工

| 诉求 | 用哪个 |
|------|--------|
| Django/apps 关单门禁（本文件） | **django-backend-check** |
| Vue 关单门禁 | `vue-frontend-check` |
| Python 深层语义质量 | `code-health-check` |
| 仅防火墙/体积扫描 | `boundary-check` |
| 功能跑测 / 验收 | `functional-testing` |
| 架构依赖分析 | `architecture-review` |
