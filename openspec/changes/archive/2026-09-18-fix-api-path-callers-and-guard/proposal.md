## Why

上一个变更（`2026-09-18-fix-auth-api-paths-and-guard`）修好了前端认证链路，但归档后主规格
`api-path-convention` 里仍有一条**当下为假**的 Scenario：

```markdown
#### Scenario: 接口测试用例
- **WHEN** 运行 `tests/api` 的接口用例
- **THEN** 全部通过（路径与路由一致）
```

实测：`tests/api/test_devices.py` → 2 passed / **7 errors**，`tests/api/test_inspector.py` → 7 passed / **9 errors**，
全部来自 `tests/api/conftest.py:34` 的 `auth_session` fixture 仍在打无尾斜杠的 `/api/auth/login` → 404 → `assert 404 == 200`。

同时暴露了**刚交付的守护自身的覆盖漏洞**：它逐行扫描源码，因此

| 漏扫的调用点 | 情况 |
|---|---|
| `tests/api/conftest.py:34` | 正是本次要修的违规点 —— 调用与字面量分处两行 |
| `frontend/src/modules/ai-assistant/api/toolbox.ts:219, 229` | 前端两处同样分行，路径写法本身正确，但从未被断言过 |

也就是说：守护在"前端 134 条字面量全部一致"的结论上少算了 2 条，且**恰好漏掉了它本该抓住的那一类**。
一个会漏扫的守护，比没有守护更危险 —— 它给出虚假的安心。

## What Changes

- **修正 `tests/api/conftest.py` 的登录路径**（补尾斜杠），让 `tests/api` 的 `auth_session` 恢复可用
- **把守护的扫描改为跨行感知**（按调用形态而非按行匹配），并按**面**扩全：
  前端 `frontend/src`、测试 `tests/**/*.py`、接口用例 `tests/api/case/*.yaml`、端点资产目录 `tools/seed_api_endpoints.py`
- **合并为单一守护模块**并建立**显式例外清单**（负向用例的路径必须登记在测试内并注明理由）
- **补一条"识别规则失效不得静默通过"的自检**（扫描量低于已知规模即失败）
- 更新 `tests/AGENTS.md` 中记录的守护文件名与覆盖范围

**Non-goals**：

- **不修端点资产目录的路由漂移** —— 实测 `tools/seed_api_endpoints.py` 中有 **52 个不同路径（61 处）已无法 resolve**
  （`/api/ai/auth/*`、`/api/cases/storage/definitions/*`、`/api/elements/dump/`、`/api/devices/<serial>/queue/*` …）。
  这是"目录 ↔ 路由表漂移"，与尾斜杠约定无关，需独立变更（见"新发现的缺口"）
- 不改后端路由、视图、中间件
- 不改 `tests/api` 的 YAML 用例（实测 45 条 `path:` 全部合规）
- 不引入前端测试基建

## 新发现的缺口（本单不处理，需独立变更）

1. **端点资产目录漂移**：52 个路径已失效（上表）。主规格里"端点资产目录中的路径 SHALL 与实际路由一致"
   这条**当前不成立**，本单只断言它的尾斜杠部分，不断言 resolve。
2. `dev_docs/DEV_TEST/接口文档/` 中若干文档仍描述"legacy 无尾斜杠路径"（`API-元素定位.md`、`API-工作流.md`、`API-测试报告.md`），
   而 legacy 路由已在上一个变更中删除 —— 接口文档与路由表同样存在漂移。

## 关联文档

- `openspec/specs/api-path-convention/spec.md` —— 本变更修改其中的需求
- `openspec/changes/archive/2026-09-18-fix-auth-api-paths-and-guard/` —— 上一个变更（守护的初次交付）
- `tests/AGENTS.md` §契约对拍测试 —— 现存范式的边界说明，本变更需要同步文件名与范围

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `api-path-convention`：修改「端到端调用方遵循唯一写法」—— 把"接口测试用例通过"这一依赖运行中服务的场景，
  换成"由默认单元守护断言"；并新增「调用面扫描的完整性与显式例外」需求。

## Impact

- **测试**：`tests/api/conftest.py`（1 行路径）、守护模块重构（`test_frontend_api_paths.py` → `test_api_path_callers.py`）、
  新增 `tests/api/test_*.py` 的恢复（不改用例本身）
- **文档**：`tests/AGENTS.md` §契约对拍测试
- **不涉及**：后端代码、前端产品代码、数据库、API 形状、依赖、构建配置
- **BREAKING**：无
