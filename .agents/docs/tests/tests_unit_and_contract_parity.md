# tests · 契约守护（单元层已退役）

> 归属模块：`tests/arch/unit/` ｜ 类型：模块功能开发说明
> 代码真相源：`tests/pytest.ini`、`tests/arch/unit/test_api_path_callers.py`、`tests/arch/unit/test_auth_endpoint_declaration.py`、`tests/arch/unit/test_auth_validation_parity.py`、`tests/arch/unit/test_auth_frontend_contract.py`
> 上级约束：根 `AGENTS.md` ｜ 模块索引：`tests/AGENTS.md`

## 单元层已退役（2026-11-24）

业务单元测试（`tests/<模块>/unit/`）已整体迁至 `temps/tests-unit-archive/`，不再进仓库、不进 CI、不要求维护。
现在的口径是：写代码时就地测一次，脚本放 `temps/`；值得长期守住的断言，改写成**灰盒用例**（走功能链路）
或本文件讲的**契约守护**（读源码断言两侧一致）。

`tests/arch/unit/` 是唯一保留的 `unit/` 目录 —— 它保留的**不是**函数实现断言，而是跨端一致性断言。

> 运行指令： `python -m pytest tests/arch/unit -v`

## 契约守护（读源码）

`tests/arch/unit/test_api_path_callers.py`、`arch/unit/test_auth_endpoint_declaration.py`、
`arch/unit/test_auth_validation_parity.py` 与 `arch/unit/test_auth_frontend_contract.py` 会**读取被测源码**做契约对拍。
这是本仓的一个例外范式，边界如下：

1. **只读**：只读 `frontend/src/**/*.{ts,vue}`、`tests/**/*.py`、`tests/api/case/*.yaml`，
   不写入、不改动这些产物。
2. **只做一致性断言**：目前只有四条 —— 全部调用方的 `/api/` 路径与后端路由表一致
   （`openspec/specs/api-path-convention`）、认证端点的鉴权姿态成对出现
   （`openspec/specs/auth-session`）、登录/注册的校验文案与数值阈值两侧一致
   （`openspec/specs/auth-form-validation`）、前端认证 DTO 与后端响应形状一致、
   拦截器的公开端点清单与网关一致（`openspec/specs/auth-response-shape` 与 `auth-session`）。
   不在这里写业务断言。
3. **零外部依赖**：不启前后端、不需凭据、不联网，因此必须留在默认套件内。
4. **按"调用形态"扫描，不按行**：调用与路径字面量分处两行时也必须被扫到。
   按行匹配的版本漏过过真实违规 —— `tests/api/conftest.py` 的登录路径、
   以及 `frontend/src/modules/ai-assistant/api/agents.ts` 的 `saveAgent`（路径先赋给 `url` 再传参）。
5. **例外必须显式**：路径断言中的例外以 `(文件, 字面量, 理由)` 三元组登记在测试内
   （前端自身路由不入断言；`test_api_path_convention.py` 的负向用例另行登记）。
   新增例外必须改测试、进 diff、被 review，不允许静默跳过。
6. **规模下限**：每个面登记扫描量下限（实测值的 ~95%）。识别规则退化时计数骤降、
   测试随即失败，而不是给出虚假的"全部一致"。**迁移单元层后「tests」面实测值下降，
   下限按新实测值重新登记，不视为退化**。

覆盖的三个面：前端 API 层、`tests` 调用面、`tests/api/case/*.yaml` 的 `path:`。
**三个面全部参与 resolve 断言**。原第四个面「端点资产目录」（`tools/seed_api_endpoints.py`）
已随元素定位的 Web/API 两域整体下线而退役（变更 remove-element-locator-web-api）。

之所以放在 Python 侧读源码：前端有独立的测试 runner（`frontend/package.json` 的 `vitest run` + `frontend/tests/**/*.spec.ts`），
但 `frontend/src` 下不放 spec；而"这条路径在后端能不能解析"只有后端能回答。
