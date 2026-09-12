---
name: boundary-check
description: |
  项目边界统一检查 — 统一检查三类边界违规：模块边界（跨 App import 内部实现、直接 ORM 写他 App 表、防火墙 #1~#4、文件体积）、引擎边界（上层 import airtest/uiautomator2、import engines.android、访问 .airtest/.u2 裸句柄）、通信通道边界（绕过前端唯一 HTTP 出口、WS 生产点≠2、agent_scope 新增 adapters/rag、上层直触引擎）。
  凡是改了 apps/ 跨模块代码、动了 import 关系或写库、改前端 HTTP 调用或后端端点、涉及引擎/device_pool，或要验收「防火墙 / 引擎边界 / 四通道」时，都应使用本 skill——即使没明说「边界检查」，只要代码里出现跨 App import、直接 ORM 写、import airtest/axios、裸 fetch，就先跑它扫一遍。
  Keywords: 边界检查, 防火墙, 跨模块, ORM写, 引擎边界, 通信通道, 通道, JWT, 模块边界, 引擎泄露, boundary check, firewall, channel
  Trigger: 架构审查 / 代码变更涉及跨模块或边界 / 改前端 HTTP 或后端端点 / 验收通信通道 / 引擎边界自查 / PR 提交前质量门禁 / 动了 import 关系或写库
---

# 项目边界统一检查

**目的**: 统一检查项目三类边界——模块边界、引擎边界、通信通道边界，杜绝越界 import / 直写他 App 表 / 引擎裸句柄泄露 / 绕过唯一 HTTP 出口。

**能力模型**: 扫描(Scan) → 诊断(Diagnose) → 报告(Report)

## 边界总览与校验工具

| 边界 | 规则要点 | 自动化校验 |
|------|---------|-----------|
| **模块边界** | 防火墙 #1~#4：service 互不 import、写走 api.py、外部走 API、不 import 内部实现；文件体积 / 模块结构 | `python tools/gen_arch_stats.py --check-boundaries [--verbose]` |
| **引擎边界** | `engines/` 唯一可触 airtest/u2；上层不 import 引擎库/具体实现、不碰 `.airtest`/`.u2` 裸句柄 | 同上（engine_leak 三类）+ `pytest tests/arch/test_channels.py::TestEngineChannel` |
| **通道边界** | 四条内部通道封闭：① HTTP REST ② WebSocket ③ AgentScope 进程内 ④ 引擎中转 | `npm run lint && npm run depcruise`（前端①）+ `pytest tests/arch/test_channels.py`（①②③④） |

---

## 一、模块边界（防火墙）

### 1.1 防火墙 #1 — service.py 互不 import

```
规则: 禁止跨 App import service / runner / consumer / callbacks / state_machine 等内部实现
检查: python tools/gen_arch_stats.py --check-boundaries（防火墙 #1 扫描）
判定: 任何命中 → 违规；现有技术债见 tools/boundary-whitelist.json
```

### 1.2 防火墙 #2 — 写操作走 api.py

```
规则: 跨 App 写（save/update/create/delete）必须走目标 App 的 api.py
检查: --check-boundaries（防火墙 #2 ORM 写扫描）
判定: 非 api.py 直接 ORM 写其他 App 的表 → 违规
```

已知技术债（TD-01~TD-05）：`state_machine.py` 直写 DeviceLock、AgentScope Tool 直写 tr_ 表等 → 见 `tools/boundary-whitelist.json`。

### 1.3 防火墙 #3 — 外部只走 HTTP API

```
规则: 外部服务不直接 import Django 内部模块
检查: grep -rn "from apps\." gateway/ --include="*.py"
说明: AgentScope 同进程调用是设计决策，不算违规（只记录依赖）。
```

### 1.4 防火墙 #4 — 不 import 他模块内部实现

```
规则: 禁止跨 App import views/service/runner 等内部文件
检查: grep -rn "from apps\.[a-z_]*\.\(views\|service\|runner\|callbacks\|state_machine\|executor\|adapter\) import" apps/ --include="*.py"
判定: 任何命中 → 违规
```

### 1.5 文件体积 / 模块结构 / 新增依赖

```
文件体积: .py ≤ 400 行、.vue ≤ 500 行（gen_arch_stats.py 扫描，超标标记需拆分）
模块结构: 每个 Django App 必须有 models.py / views.py / api.py / urls.py
新增依赖: git diff 新增 "from apps.{其他app}" 行 → 需架构师 review
```

---

## 二、引擎边界（L1c engines/）

```
规则: engines/ 是唯一可触碰第三方引擎库（airtest/uiautomator2）的层；
      上层（apps/ · gateway/）只经 engines.base.UiEngine 协议 + engines.registry 工厂消费设备能力。
检查: python tools/gen_arch_stats.py --check-boundaries [--verbose]
      三类泄漏：engine_lib（import 引擎库）/ engine_impl（import engines.android.*）/ raw_handle（访问 .airtest/.u2）
      --verbose 打印全部已知技术债明细（file:line + 类别 + 片段 + 白名单修复说明），并落日志 logs/boundary-check.log
判定: 新增命中 → 违规；现有技术债登记于 tools/boundary-whitelist.json（pattern="engine-leak"，TD-06）
补充: pytest tests/arch/test_channels.py::TestEngineChannel（上层不 import 引擎库的单元断言）
```

---

## 三、通信通道边界（四条内部通道）

> 规则真相源：`android-autotests-rules/references/architecture.md` §一（逐通道「链路 / 能做 / 不能做 / 校验」）。

### ① 前端 ↔ Django — HTTP REST + JWT

```
规则: 链路 = 组件 → 模块 api.ts → shared/api-client.ts（唯一 HTTP 出口）→ /api/... DRF
校验（自动）:
  1. 前端出口: cd frontend && npm run lint && npm run depcruise
     - lint: no-restricted-imports（禁 axios/ky/got/superagent）+ no-restricted-globals（禁 fetch/XMLHttpRequest）+ no-restricted-syntax（禁 sendBeacon）
     - depcruise: 只有 api-client.ts + api-auth-interceptors.ts 能依赖 axios
  2. 后端 JWT: pytest tests/arch/test_channels.py::TestHttpChannel
     - baseURL == "/api"、业务路由挂 /api/、PUBLIC_PREFIXES 不含业务路由
校验（补充 grep，尚未自动化）:
  - 返回非 REST: grep -rn "render(request\|TemplateResponse\|render_to_string" apps/ --include="*.py"
  - 通道外协议: grep -rn "grpc\|kafka\|rabbitmq\|graphql\|mqtt\|webrtc" apps/ gateway/ --include="*.py" -i
```

### ② Django → 前端 — WebSocket + JWT

```
规则: 仅 1 个 WS 生产点（编辑锁），Consumer 必须在 gateway/routing.py 注册
校验: pytest tests/arch/test_channels.py::TestWebSocketChannel（len(websocket_urlpatterns) == 1）
```

### ③ AgentScope → Django — 进程内直接调用

```
规则: agent_scope 工具经各 App api.py 白名单调用；禁止直连 DB/设备；禁止新增 adapters/ 或 rag/
校验: pytest tests/arch/test_channels.py::TestAgentScopeChannel（无 adapters/、rag/）
```

### ④ Django ↔ 设备 — 引擎中转（UiEngine 协议）

```
规则: 上层经 UiEngine 协议 → engines/ → 设备；Django 不关心引擎内部 ADB/Airtest/u2
校验: pytest tests/arch/test_channels.py::TestEngineChannel + gen_arch_stats --check-boundaries（engine_leak）
```

---

## 工作流

### 快速扫描（改完即跑，<5 秒）

```bash
# 模块边界 + 引擎边界
python tools/gen_arch_stats.py --check-boundaries

# 通道边界（前端）
cd frontend && npm run lint && npm run depcruise
```

### 完整扫描（架构审查 / PR 门禁，~30 秒）

```bash
# 1. 模块 + 引擎边界（防火墙 #1/#2 + engine_leak，含白名单）
python tools/gen_arch_stats.py --check-boundaries --verbose

# 2. 通道边界断言（四条通道的结构不变量）
pytest tests/arch/test_channels.py -v -m arch

# 3. 前端唯一出口（ESLint 单文件 + dependency-cruiser 依赖图）
cd frontend && npm run lint && npm run depcruise

# 4. 补充 grep（非 REST / 通道外协议）
grep -rn "render(request\|TemplateResponse\|render_to_string" apps/ --include="*.py"
grep -rn "grpc\|kafka\|rabbitmq\|graphql\|mqtt\|webrtc" apps/ gateway/ --include="*.py" -i
```

---

## 输出格式

```
🔍 项目边界检查报告 — {timestamp}
─────────────────────────────────────────────
模块边界（防火墙 #1/#2/#3/#4）:  ✅ 通过 / ⚠️ N 处（含 M 处已知）
引擎边界（engine_lib/impl/raw）:  ✅ 通过 / ⚠️ N 处新违规（含 M 处已知）
通道① HTTP（前端出口 + JWT）:      ✅ 通过 / ⚠️
通道② WS（2 生产点）:              ✅ 通过 / ⚠️
通道③ AgentScope（无 adapters/rag）: ✅ 通过 / ⚠️
通道④ 引擎中转（不 import 引擎库）:  ✅ 通过 / ⚠️
文件体积 / 模块结构:                ✅ 通过 / ⚠️ N 处
─────────────────────────────────────────────
总评: 🟢 健康 / 🟡 需关注 / 🔴 需修复
```

---

## 关联文件

| 文件 | 说明 |
|------|------|
| `android-autotests-rules/references/architecture.md` | §一 通道规则 · §二 依赖方向 · §七 引擎边界 |
| `android-autotests-rules/references/api-conventions.md` | 三道防火墙完整规则 |
| `tools/gen_arch_stats.py --check-boundaries` | 防火墙 #1/#2 + 引擎边界自动校验（含白名单） |
| `tools/boundary-whitelist.json` | 已知技术债白名单（TD-01~TD-06） |
| `tests/arch/test_channels.py` | 四条通道的结构不变量 pytest 断言 |
| `frontend/eslint.config.js` + `.dependency-cruiser.cjs` | 前端唯一出口（ESLint + 依赖图） |
