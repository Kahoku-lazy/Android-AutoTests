# Auth API 自动化测试

认证模块 5 个端点，**72 条用例**。

| 端点 | 文件 | 用例数 | 状态 |
|------|------|:------:|------|
| `POST /api/ai/auth/login` | `test_login.py` | 20 | ✅ 全部通过 |
| `POST /api/ai/auth/register` | `test_register.py` | 24 | ✅ 全部通过 |
| `POST /api/ai/auth/refresh` | `test_refresh.py` | 10 | ✅ 7 通过 / 2 xfail |
| `POST /api/ai/auth/logout` | `test_logout.py` | 9 | ✅ 3 通过 / 5 xfail / 1 skip |
| `GET /api/ai/auth/me` | `test_me.py` | 9 | ✅ 6 通过 / 3 xfail |

> ⚠️ **已知问题**：`/api/ai/auth/me` 和 `/api/ai/auth/logout` 的 URL 匹配
> 中间件公开路径前缀 `/api/ai/auth/`，导致中间件跳过鉴权，两个端点无法通过
> HTTP 获取 `user_id`。10 条涉及鉴权的用例用 `@pytest.mark.xfail` 标记，
> 修复 `gateway/middleware.py` 的公开路径配置后自动生效。

## 架构

三层分离：**Schema（结构契约）→ Data（用例数据）→ Runner（执行引擎）**。

```
tests/auth/
├── conftest.py          # 共享基础设施：端点常量、auth_token fixture
├── schemas.py           # JSON Schema — 响应结构契约（6 个 Schema）
├── test_login.py        # 登录：2 参数化组 + 5 独立函数 = 20 条
├── test_register.py     # 注册：3 参数化组 + 2 独立函数 = 24 条
├── test_refresh.py      # 刷新：1 参数化组 + 4 独立函数 = 10 条
├── test_logout.py       # 登出：2 参数化组 + 4 独立函数 = 9 条
└── test_me.py           # 当前用户：1 参数化组 + 3 独立函数 = 9 条
```

### 为什么不是 44 个独立函数？

分析发现 44 条用例的断言逻辑只有 **5 种模式**（Shape）：

| Shape | 状态码 | 登录 | 注册 | 处理方式 |
|-------|:------:|:----:|:----:|----------|
| 校验拒绝 | 400 + 精确 message | 8 | 15 | `@pytest.mark.parametrize` |
| 认证失败 | 401 + 固定 message | 7 | — | `@pytest.mark.parametrize` |
| 注册成功 | 200 + Token 结构 | 1 | 2 | `@pytest.mark.parametrize` |
| 条件分支 | 200 / 409 | — | 5 | `@pytest.mark.parametrize` |
| 边界/安全 | 混合逻辑 | 4 | 2 | 独立函数 |

相同 Shape 的用例只是 **数据不同**（请求体、期望消息），执行逻辑完全一致。
参数化后：15 个校验拒绝用例共享 1 个执行函数，新增用例只需追加 8 行数据。

### JSON Schema 的角色

取代分散的字段断言，一次定义全局复用：

```python
# 之前：5 个分散的 assert
assert body["status"] is True
assert "access_token" in body
assert "refresh_token" in body
assert body["token_type"] == "bearer"
assert "user" in body

# 之后：1 个 Schema 校验
jsonschema.validate(instance=body, schema=AUTH_SUCCESS_SCHEMA)
```

Schema 同时是 **可执行文档**——一眼看清 API 响应结构，变更时只改一处。

### 数据驱动示例

```python
# 新增一条校验拒绝用例：追加 8 行数据
ValidationCase(
    id="TC-REG-XXX",
    title="新校验规则",
    description="请求体：...\n期望：400，message=\"...\"\n测试点：...",
    severity="normal", priority="P1",
    payload={"username": "test", ...},
    expected_status=400, expected_message="错误消息",
)
```

不需写函数、不用加装饰器，Allure 报告自动生成。

---

## 环境配置

### 依赖

已包含在项目 `requirements.txt` 中：

```
pytest>=8.0
pytest-django>=4.0
allure-pytest>=2.13
requests>=2.30
jsonschema>=4.0          # JSON Schema 校验
```

### 被测服务

默认连接 `http://localhost:8766`。可通过环境变量覆盖：

```bash
# Windows (PowerShell)
$env:TEST_BASE_URL = "http://192.168.1.100:8766"

# macOS / Linux
export TEST_BASE_URL=http://192.168.1.100:8766
```

### 平台账号

注册测试依赖 `admin` 用户已存在（用于 TC-REG-020 重复用户名检测），登录测试依赖 `admin / admin123` 凭据有效。

---

## 运行

> **注意**：Windows 下 `pytest` 可能不在 PATH 中，统一使用 `python -m pytest`。

### 全部认证测试

```bash
python -m pytest tests/auth/ -v
```

### 按端点筛选

```bash
python -m pytest tests/auth/test_login.py -v      # 登录 20 条
python -m pytest tests/auth/test_register.py -v   # 注册 24 条
```

### 按标记筛选

```bash
python -m pytest tests/auth/ -v -m api            # 所有接口测试
python -m pytest tests/auth/ -v -m "api and auth" # 认证接口测试
python -m pytest tests/auth/ -v -k "success"      # 按名称匹配
```

### 生成 Allure 报告

```bash
python -m pytest tests/auth/ -v --alluredir=tests/allure-results
allure serve tests/allure-results
```

报告按 feature（认证模块）、story（登录/注册接口）、severity
（BLOCKER/CRITICAL/NORMAL/MINOR）三维分类，支持按标签筛选。

### 单条用例（参数化 ID）

```bash
pytest tests/auth/test_register.py -v -k "TC-REG-001"
pytest tests/auth/test_login.py -v -k "TC-LOGIN-013"
```

---

## 文件对照

| 旧文件（已删除） | 新文件 | 用例数 |
|---|---|---|
| `tests/login/test_api.py` (454 行) | `tests/auth/test_login.py` | 20 |
| `tests/register/test_api.py` (632 行) | `tests/auth/test_register.py` | 24 |
| — | `tests/auth/test_refresh.py` | 10 |
| — | `tests/auth/test_logout.py` | 9 |
| — | `tests/auth/test_me.py` | 9 |
| — | `tests/auth/schemas.py` | — |
| — | `tests/auth/conftest.py` | — |
| **1086 行** | **~1600 行** | **72** |
