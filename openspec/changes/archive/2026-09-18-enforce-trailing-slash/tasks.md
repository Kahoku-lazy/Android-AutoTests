## 1. 变更与规格

- [x] 1.1 `openspec/changes/enforce-trailing-slash/` 四件套
- [x] 1.2 新能力 `specs/api-path-convention/spec.md`；`specs/api-path-normalization/spec.md` 的 REMOVED delta
- [x] 1.3 `openspec validate enforce-trailing-slash` 通过 —— `Change 'enforce-trailing-slash' is valid`

## 2. 路由统一（非破坏，中间件暂留）

- [x] 2.1 `apps/*/urls.py` 的 111 条手写 `path()` 补尾斜杠（无 `re_path`，机械化改写） —— 分两轮：先 111 条同行写法，再补 7 条「路径串独占一行」的多行 `path(`（正则漏了它们）；另有 29 条来自 `ai_assistant` 的 `DefaultRouter(trailing_slash=False)`，改为默认
- [x] 2.2 验证：遍历 `get_resolver()`，全部 `/api/` 路由均以 `/` 结尾 —— `temps/check_routes.py`：275→256 条，尾斜杠形态 180 + `.json` 后缀分支 76，**0 违规**
- [x] 2.3 验证：`manage.py check`；老写法 `POST /api/auth/login` 仍可命中（中间件补斜杠） —— `manage.py check` 通过；此时中间件仍在，老写法仍可命中（非破坏）

## 3. 关闭 301

- [x] 3.1 `config/settings.py` 增加 `APPEND_SLASH = False` —— `APPEND_SLASH = False`，注释写明它关掉的是 301 那条有害路径
- [x] 3.2 验证：缺失斜杠不产生 3xx —— 由 `test_api_path_convention.py::test_missing_slash_never_redirects` 断言不得出现 3xx

## 4. 调用方收敛

- [x] 4.1 前端 api 层路径补 `/` —— 129 个调用点（含此前漏扫的 `djangoClient`）全部补齐，复扫 0 缺
- [x] 4.2 `tests/api/case/*.yaml`（45 处）路径补 `/` —— 43 处；`tests/graybox/unit/**` 下硬编码 `/api/` 的用例另补 33 处（原任务漏列了 Python 用例）
- [x] 4.3 `tools/seed_api_endpoints.py`（183 处端点资产）路径补 `/` —— `seed_api_endpoints.py` 175 处 + `seed_api_schemas.py` 1 处
- [x] 4.4 验证：前端构建/类型检查通过；`pytest tests/api -q` 通过（需 live server） —— `vue-tsc` 30 个错误 = 既有基线（无新增）；后端全量灰盒 273 passed

## 5. 删除中间件

- [x] 5.1 删除 `gateway/normalize_slash.py` 与 `MIDDLEWARE` 中的项 —— 删除 `gateway/normalize_slash.py` 与 `MIDDLEWARE` 首项；`managed.py check` 通过
- [x] 5.2 删除 `tests/graybox/unit/test_trailing_slash_tolerance.py`（其断言的是被移除的能力） —— 删除 `test_trailing_slash_tolerance.py`（其断言的能力已不存在）
- [x] 5.3 新增严格语义用例：缺失尾斜杠 → 404、路由表全部带斜杠、不产生 3xx —— 新增 `test_api_path_convention.py`（11 项）：路由表全带斜杠 / 缺失即 404（公开与已鉴权两条路径）/ 不得 3xx / 带斜杠命中视图
- [x] 5.4 更新 `temps/login-backend-map`：受管清单移除该中间件、D 节结论改为严格语义 —— 受管文件 16→15，中间件 12→11 道，新增 `trailing_slash_missing` 实测；指纹 `c0f0da6ede7e`

## 6. 文档与 schema

- [x] 6.1 `dev_docs` 中约 502 处路径引用补 `/` —— `dev_docs` 11 个文件补 153 处，无双重斜杠
- [x] 6.2 OpenAPI schema 重新生成并核对路径全带斜杠 —— SchemaGenerator 实测 **128 条路径 0 条缺尾斜杠**
- [x] 6.3 `apps/accounts/AGENTS.md` 路径约定改为严格表述 —— 改为「路径必须带尾斜杠；`POST /api/auth/login` 是 404」并指向 `api-path-convention`

## 7. 门禁

- [x] 7.1 `manage.py check` / `ruff` / `format` / `gen_arch_stats.py --check-boundaries` —— check / ruff / format / 边界检查全部通过
- [x] 7.2 `pytest tests/graybox/unit`（全量）+ `pytest tests/arch` —— `tests/graybox/unit` **273 passed**（含新用例）；`tests/arch` **34 passed**
- [x] 7.3 归档并同步 delta 到主规格
## 8. 实施期发现（方案 B 的实质内容，原任务未预见）

- [x] 8.1 **统一尾斜杠暴露出重复路由注册**：`element_locator` 把同一资源注册了两遍 —— router 与 legacy 手写路由，
  此前靠「无斜杠→legacy / 带斜杠→router」同时存活，**两套返回形状不同**（legacy 平铺 `{status, groups}` + 全量 + `endpoint_count`；
  router 信封 `{status, data}` + 仅顶层树）。用户选择 **B：router 权威**，已删除 18 条被遮蔽的 legacy 路由，
  并把 `test_element_locator_views_split.py` 的护栏从「legacy 路由不变」改为「迁移后的路径仍由对应 ViewSet 服务」
- [x] 8.2 **`views_drf.py` 的写路径语义被修正**：原 `perform_create/update` 抛 `ValidationError`（→**400**），
  而 legacy 的 `group_write_gone` 是**无条件 410** —— 空 body 会先变成 400，丢掉「接口已停用」的语义。
  改为 `GroupWriteRetiredMixin` 覆盖 `create/update/partial_update/destroy`（`APIException` 需在模块级导入，
  否则模块导入即 NameError）
- [x] 8.3 **前端迁移成本远低于预估**：前端 `api.ts` 只有 6 个函数被真正调用（其余 ~10 个是死代码），
  且 `createdLeafId()` 本就同时兼容信封与平铺两种形状 → 形状迁移零成本，只需改路径
- [x] 8.4 **产物采集器自身也是调用方**：它用无斜杠路径发请求，必须同步；并新增
  `trailing_slash_missing` 的实测，让 D 节结论由「实测值」驱动而非叙述
- [x] 8.5 **产物生成器的一个真回归**：`renderEndpoints` 按字面路径查实测卡，路由加斜杠后 key 失配、
  5 张卡全部丢失；改为斜杠无关查表。自检器抓到了它
- [x] 8.6 `test_workflow_directory_update.py` 的 `DIRECTORIES_PATH` 是**基址**（派生串自带斜杠），
  盲替换会造出双斜杠 → 已回退该常量并加注释说明
- [x] 8.7 两个 ViewSet 里各自内嵌了一份 `Gone` 异常类，已在收敛写路径时统一为模块级 `GroupWriteRetired`
