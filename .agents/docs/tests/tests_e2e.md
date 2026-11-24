# tests · 浏览器 b2b 层（Playwright）

> 归属模块：`tests/<模块>/e2e/`、`tests/e2e/` ｜ 类型：模块功能开发说明
> 代码真相源：`tests/e2e/conftest.py`、`tests/e2e/selectors.py`、`tests/e2e/step_report.py`、`tests/pytest.ini`
> 上级约束：根 `AGENTS.md` ｜ 模块索引：`tests/AGENTS.md`

## b2b 是什么口径

真实浏览器点真实界面，断言**用户看得见的反馈**：提示词、弹窗、Toast、列表变化。
专测"有交互提示词"的功能 —— 接口已经成功的功能，前端仍可能漏弹"新建已完成"、弹错文案、或者压根没刷新列表。

- 落位：`tests/<模块>/e2e/`，文件以 `test_` 开头；共享设施在 `tests/e2e/`。
- 颗粒度与灰盒一致：**一个交互功能一条用例**（点一次完整链路），不按按钮 / 组件拆。

> 运行指令： `python -m pytest tests/<模块>/e2e -q`（共享设施：`tests/e2e/`）

## 断言什么

1. **提示词 / 弹窗**：成功后是否出现预期文案（如"新建已完成"）、失败后是否给出可读错误。
2. **列表与跳转**：新建 / 删除后列表是否即时变化、是否跳回正确页面。
3. **落库联动**：需要时在同一用例里用接口或 ORM 复核一次（浏览器是入口，库里是真值）。

例：工作流新建 —— 打开工作流页 → 填名称 → 提交 → 断言"新建已完成"弹窗出现 → 列表出现新行 → 关闭弹窗。

## 规则

1. 端到端用例放 `tests/<模块>/e2e/`；选择器常量集中在 `tests/e2e/selectors.py`，用例里禁止散写字面选择器。
2. 业务编号 `BF-##` / `TC-BF-UI-###` / `TC-SESSION-###` 与端到端 `E2E-###` 一一对应，映射写在用例 docstring 里。
3. **零密钥**：本层不使用 `TEST_ADMIN_PASSWORD`。`conftest.py` 用公开注册端点自建固定账号 `e2e_probe` 并在后续运行中复用，因此不带任何环境变量也能跑，不会静默跳过。
4. 前后端需已启动（`python run.py start`，前端 5173 / 后端 8766）；不可达时整组 skip —— 那是环境不可达，不是用例缺陷。
5. **每步留痕**：动作与断言都走 `steps` 夹具（`tests/e2e/step_report.py`）—— `click` / `fill` / `press` / `long_press` / `scroll` 会在截图上标注「点了哪里 / 输了什么 / 滑了多远」，`inspect` 用元素局部放大图给断言留痕。密码类输入在报告里一律脱敏。
6. **步骤报告**：跑完自动生成 `tests/reports/e2e/index.html`（HTML + `shots/*.jpg`，图片压缩到宽 1100px），按用例展示步骤时间线，缩略图列宽缩放、点击看大图。**不需要额外参数**，成败都落盘。
7. pytest-html 报告（可选，与步骤报告互不影响）： `python -m pytest tests/<模块>/e2e --html=tests/reports/e2e.html --self-contained-html`。

## 现状与缺口

目前只有 1 条 b2b 用例（`tests/auth/e2e/test_login_e2e.py` 登录链路）。有提示词的功能（工作流新建、平台助手新建/删除、
用例导入、模型配置保存等）**尚未覆盖**，新增 b2b 用例优先补这些面。
