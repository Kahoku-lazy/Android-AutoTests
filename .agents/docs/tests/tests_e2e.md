# tests · 端到端测试

> 归属模块：`tests/<模块>/e2e/`、`tests/e2e/` ｜ 类型：模块功能开发说明
> 代码真相源：`tests/e2e/conftest.py`、`tests/e2e/selectors.py`、`tests/e2e/step_report.py`、`tests/pytest.ini`
> 上级约束：根 `AGENTS.md` ｜ 模块索引：`tests/AGENTS.md`

## 端到端测试

> 运行指令： `python -m pytest tests/<模块>/e2e -q`（共享设施：`tests/e2e/`）

1. 端到端用例放 `tests/<模块>/e2e/`，文件以 `test_` 开头；选择器常量集中在 `tests/e2e/selectors.py`，用例里禁止散写字面选择器。
2. 业务编号 `BF-##` / `TC-BF-UI-###` / `TC-SESSION-###` 与端到端 `E2E-###` 一一对应，映射写在用例 docstring 里。
3. **零密钥**：本层不使用 `TEST_ADMIN_PASSWORD`。`conftest.py` 用公开注册端点自建固定账号 `e2e_probe` 并在后续运行中复用，因此不带任何环境变量也能跑，不会静默跳过。
4. 前后端需已启动（`python run.py start`，前端 5173 / 后端 8766）；不可达时整组 skip —— 那是环境不可达，不是用例缺陷。
5. **每步留痕**：动作与断言都走 `steps` 夹具（`tests/e2e/step_report.py`）—— `click` / `fill` / `press` / `long_press` / `scroll` 会在截图上标注「点了哪里 / 输了什么 / 滑了多远」，`inspect` 用元素局部放大图给断言留痕。密码类输入在报告里一律脱敏。
6. **步骤报告**：跑完自动生成 `tests/reports/e2e/index.html`（HTML + `shots/*.jpg`，图片压缩到宽 1100px），按用例展示步骤时间线，缩略图列宽缩放、点击看大图。**不需要额外参数**，成败都落盘。
7. pytest-html 报告（可选，与步骤报告互不影响）： `python -m pytest tests/e2e --html=tests/reports/e2e.html --self-contained-html`。
