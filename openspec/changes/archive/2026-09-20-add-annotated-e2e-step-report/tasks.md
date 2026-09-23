## 1. 报告引擎

- [x] 1.1 新增 `tests/e2e/step_report.py`：`Mark` / `annotate()`（点击点、目标矩形、序号徽标、顶部说明条、滚动箭头）+ 中文字体候选探测；验证：临时脚本画一张样例图并用 modlens 读图确认中文与标注可辨。
- [x] 1.2 实现 `StepReport`（reset / save_image / render）与 `CaseRecord`/`Step` 数据类，图片按宽 1100px 压 JPEG；验证：跑单条用例后 `tests/reports/e2e/shots/` 出现 jpg 且单张 < 200KB。
- [x] 1.3 实现 HTML 渲染（遵循 html-report 规范 token：暖色纸面、圆角 12/18、body 字重 500、卡片无阴影 hover 上浮、强调色 #19c8b9、禁止冷蓝）：头部环境与 KPI、目录、按用例分组的步骤时间线、缩略图固定列宽 + 灯箱大图 + 打开原图；验证：生成 `index.html` 并用 Playwright 打开截图核对版式。
- [x] 1.4 实现 `StepRecorder`（shot / inspect / click / fill / press / long_press / scroll / fail），动作仍由 Playwright 原生 API 完成；验证：15 条用例全部改用记录器后仍全绿。

## 2. 夹具与钩子

- [x] 2.1 `tests/e2e/conftest.py` 新增会话级 `e2e_step_report` 与用例级 `steps` 夹具，会话开始时清理上次产物；验证：连续跑两次不残留上一轮的图片。
- [x] 2.2 `pytest_runtest_makereport` 记录用例状态/耗时/异常，失败时追加「用例失败」步骤（含异常文本），并保留原有 Allure 失败截图；验证：故意改坏一条断言，报告里该用例为失败且带异常文本与失败截图。
- [x] 2.3 `pytest_sessionfinish` 落盘报告；验证：不带 `--html` 也生成 `tests/reports/e2e/index.html`。

## 3. 用例改造

- [x] 3.1 15 条用例逐个把动作与断言换成 `steps.*` 调用，密码类输入一律 `secret=True`；验证：报告里每步都有截图，且口令不以明文出现。
- [x] 3.2 跳转类步骤（登录成功 / 注册成功 / 登出 / 守卫）用无标注 `shot()`，坐标类标注只用在原地动作上；验证：通读报告，标注框都落在正确元素上。
- [x] 3.3 断言步骤用 `inspect()` 局部截图（按钮态、错误文案、窄屏可达性）；验证：局部图能看清被断言的状态。

## 4. 验证与文档

- [x] 4.1 全量跑绿并连跑两次：`python -m pytest tests/e2e -q`；验证：15 passed ×2，且报告用例数与步骤数一致。
- [x] 4.2 报告体积与加载检查：统计 `tests/reports/e2e` 总大小与单图大小；验证：总大小在可接受范围（目标 < 15MB），HTML 打开不卡。
- [x] 4.3 失败路径实测：临时把一条断言改错跑一次，确认报告出现失败用例 + 异常文本 + 失败截图，然后恢复；验证：恢复后再跑全绿。
- [x] 4.4 文档同步：`tests/AGENTS.md` 端到端节补报告说明；功能测试文档第四节补报告路径与查看方式；PRD「怎么跑这些测试」补报告命令；验证：按文档命令能直接打开报告。
- [x] 4.5 归档前回归：`python -m pytest tests/graybox/unit -q` 结果与变更前一致（300 passed）。
