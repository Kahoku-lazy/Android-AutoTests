## Why

`tools/seed_api_endpoints.py` 的 docstring 写着 "Seed ApiGroup + ApiEndpoint records from the platform's own API catalog"
—— 它的定位是**平台 API 的镜像**，用于填充元素定位模块的接口资产库（供接口测试选用）。
但它已经严重漂移：按括号配对解析（该文件大量调用是**跨行**书写，单行正则会漏掉七成），
实测 **187 个条目里有 61 条**指向已不存在的路由：

| 类别 | 条数 | 例 |
|---|---|---|
| 可确认改名 | 5 | `/api/ai/auth/*` → `/api/auth/*`（网关 `RETIRED_AUTH_PATHS` 列的就是这 5 条） |
| 与现有条目重复 | 1 | `/api/ai/health/`（目录中已有 `/api/ai/agents/health/`） |
| 无任何对应物 | 55 | `/api/runner/*`、`/api/cases/{storage,api-testing,web}/definitions/*`、`/api/elements/{dump,action,device-info,screenshot}/` … |

指向不存在端点的资产拿去做接口测试没有意义；这也是上一轮守护只能对它"退化为只断言尾斜杠"的原因
（`tests/graybox/unit/test_api_path_callers.py` 里的显式说明）。

## What Changes

- **5 条改名**：`/api/ai/auth/*` → `/api/auth/*`（目录中不存在 `/api/auth/*`，不会产生重复）
- **56 条删除**：1 条重复项 + 55 条无对应物的条目
- **11 个空分组/目录删除**：删完条目后不再被引用的 `create_group` / `create_folder` 语句
  （`g_case_storage`、`g_run_mgmt`、`f_runner` …）
- **守护升级**：`test_api_path_callers.py` 把端点资产目录纳入 **resolve 断言**（此前只断言尾斜杠），
  目录面规模下限随之按实测调整
- 更新 `tests/AGENTS.md`：去掉"目录只断言写法"的说明

**Non-goals**：

- 不改任何后端路由或视图 —— 漂移在目录侧，不在路由侧
- 不新增 `is_implemented` 之类的字段（目录定位是"镜像"，不是"规划面"）
- 不重建目录内容（不补新增端点的条目）—— 补齐是另一件事，本变更只做对账

## 关联文档

- `openspec/specs/api-endpoint-catalog/spec.md` —— 本变更新建的能力
- `openspec/specs/api-path-convention/spec.md` —— 本次移除其中"目录一致性不成立"的临时说明
- `tests/AGENTS.md` §契约对拍测试 —— 边界说明

## Capabilities

### New Capabilities

- `api-endpoint-catalog`：端点资产目录必须与后端路由表一致，且该一致性由默认测试守护

### Modified Capabilities

- `api-path-convention`：移除"端点资产目录与路由表的一致性当前不成立"这一临时说明，
  并把目录纳入 resolve 断言覆盖范围

## Impact

- **工具与数据**：`tools/seed_api_endpoints.py`（187 → 131 个条目）
- **测试**：`tests/graybox/unit/test_api_path_callers.py`（目录面纳入 resolve；规模下限）
- **文档**：`tests/AGENTS.md`
- **不涉及**：后端代码、数据库结构、API 形状、依赖
- **BREAKING**：无（删除的是指向不存在端点的资产条目；重新执行该 seed 脚本后目录即与路由表一致）
