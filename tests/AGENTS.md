
## 简介

负责平台的测试工作，测试范围有接口、单元测试、集成测试、端到端测试，对应的测试信息详细阅读对应的模块。


## 代码规范

1. 所有的测试用例文件名称**必须**以 `test_` 开头。
2. 测试报告统一输出到 `reports/`目录


## 单元测试

> 运行指令： `python -m pytest tests/graybox/unit -v`

1. 单元测试用例路径： `tests/graybox/unit`，文件以 `test_` 开头。
2. 单元测试文档路径： `dev_docs/05-开发与测试/单元测试文档`

### 契约对拍测试（读源码）

`tests/graybox/unit/test_api_path_callers.py`、`test_auth_endpoint_declaration.py`、
`test_auth_validation_parity.py` 与 `test_auth_frontend_contract.py` 属于单元层，
但它们会**读取被测源码**做契约对拍。这是本仓的一个例外范式，边界如下：

1. **只读**：只读 `frontend/src/**/*.{ts,vue}`、`tests/**/*.py`、`tests/api/case/*.yaml`、
   `tools/seed_api_endpoints.py`，不写入、不改动这些产物。
2. **只做一致性断言**：目前只有四条 —— 全部调用方的 `/api/` 路径与后端路由表一致
   （`openspec/specs/api-path-convention`）、认证端点的鉴权姿态成对出现
   （`openspec/specs/auth-session`）、登录/注册的校验文案与数值阈值两侧一致
   （`openspec/specs/auth-form-validation`）、前端认证 DTO 与后端响应形状一致、
   拦截器的公开端点清单与网关一致（`openspec/specs/auth-response-shape` 与 `auth-session`）。
   不在这里写业务断言。
3. **零外部依赖**：不启前后端、不需凭据、不联网，因此必须留在默认单元套件内。
   需要显式开启才能跑的检查（例如 `tests/e2e` 的登录用例，依赖 `TEST_ADMIN_PASSWORD`）
   在默认门禁里是静默跳过的，起不到守护作用。
4. **按"调用形态"扫描，不按行**：调用与路径字面量分处两行时也必须被扫到。
   按行匹配的版本漏过过真实违规 —— `tests/api/conftest.py` 的登录路径、
   以及 `frontend/src/modules/ai-assistant/api/toolbox.ts` 的两处调用。
5. **例外必须显式**：路径断言中的例外以 `(文件, 字面量, 理由)` 三元组登记在测试内
   （前端自身路由不入断言；`test_api_path_convention.py` 的负向用例另行登记）。
   新增例外必须改测试、进 diff、被 review，不允许静默跳过。
6. **规模下限**：每个面登记扫描量下限（实测值的 ~95%）。识别规则退化时计数骤降、
   测试随即失败，而不是给出虚假的"全部一致"。

覆盖的四个面：前端 API 层、`tests` 调用面、`tests/api/case/*.yaml` 的 `path:`、端点资产目录。
**四个面全部参与 resolve 断言** —— 端点资产目录（`tools/seed_api_endpoints.py`）已对账到路由表
（5 条改名、56 条失效项删除），它再漂移会直接失败。

之所以放在 Python 侧读源码：前端没有测试运行器（`frontend/src` 下无 spec/test 文件），
而"这条路径在后端能不能解析"只有后端能回答。

## 集成测试

> 运行指令： `python -m pytest tests/graybox/integration -v`

1. 集成测试用例路径： `tests/graybox/integration`，文件以 `test_` 开头。
2. 集成测试文档路径： `dev_docs/05-开发与测试/集成测试文档`

## 接口测试

> 运行指令： `python -m pytest tests/api -v`

1. 接口文档路径： `dev_docs/05-开发与测试/接口文档`
2. 接口测试用例路径： `tests/api`
3. 接口测试使用Jsonschema来断言响应结果，测试用例使用YAML编写，文件放在tests/api/case中。YAML用例要有测试标题，测试点

## 接口测试脚本与模块映射

> 按模块划分「哪些脚本测哪些功能」，运行指令与路径见「接口测试」节；模块 marker 见 pytest.ini。

| 模块 | 测试脚本 | YAML 用例 | 覆盖功能 |
|---|---|---|---|
| 登录鉴权 | tests/api/test_login_page.py | case/login.yaml、case/register.yaml | 登录 / 注册 |
| 设备管理 | tests/api/test_devices.py | case/devices.yaml | 设备列表 / 锁定 / 连接 / 断开 / 释放 / 心跳 / 当前设备 |
| 设备检查器 | tests/api/test_inspector.py | case/inspector.yaml | 快照抓取 / 列表 / 详情 / 结构分析 / 删除 / 保存到元素定位 / 页面回看 |

> 其余模块（元素定位 / 用例管理 / 执行引擎 / 测试报告 / AI 助手 / 工作流 / 评估器）接口测试脚本待补充。
