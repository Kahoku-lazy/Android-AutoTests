## Why

端到端层现在能跑（15 条），但**跑完看不出「点了哪里、输了什么、为什么失败」**：Playwright 的失败截图是整屏无标注的原图，成功路径则完全没有留痕。审查一条失败用例时，只能靠读代码还原操作序列，效率低且容易误判。

需求（用户原话）：「端到端测试每步要有截图，截图上要标注点击了什么，滑动的位置，输入的位置等信息」+「做出 HTML 报告形式，截图太大在 HTML 上要缩放，HTML 上显示步骤与截图」。

## What Changes

- **新增 `tests/e2e/step_report.py`** —— 步骤报告引擎（Pillow 在截图上画标注，零新依赖）：
  - 标注类型：**点击**（目标矩形 + 点击点十字 + 序号徽标）· **输入**（目标矩形 + 输入内容，密码脱敏为 `••••`）· **按键**（目标矩形 + 按键名）· **长按**（目标矩形 + 按住时长）· **滚动/滑动**（方向箭头 + 距离）；
  - 每张截图顶部画说明条：`步骤 N · 这一步做了什么`；
  - 断言类步骤额外提供**元素局部放大截图**（比整屏更容易看清按钮态与文案）；
  - 图片统一压到宽 1100px 的 JPEG（q=82），避免报告膨胀；
  - 生成**单个 HTML 报告** `tests/reports/e2e/index.html`：头部环境与 KPI、目录、按用例分组的步骤时间线，**图片按列宽缩放显示**，点击弹出大图（灯箱，ESC/点空白关闭）+「打开原图」链接。
- **改造 15 条登录页端到端用例** —— 每个动作与断言都通过 `steps` 夹具执行并留痕（`steps.click/fill/press/long_press/scroll/shot/inspect`），动作语义仍由 Playwright 原生 API 完成，夹具只负责标注与记录。
- **`tests/e2e/conftest.py`** —— 新增 `steps`（用例级记录器）与 `e2e_step_report`（会话级报告）夹具；`pytest_runtest_makereport` 记录用例结果、失败时补一张「用例失败」步骤（带异常文本）；`pytest_sessionfinish` 落盘 HTML。失败截图同时继续挂 Allure（保持既有约定）。
- **文档同步** —— `tests/AGENTS.md` 端到端节补报告说明；功能测试文档第四节补报告路径与查看方式；PRD 测试章的「怎么跑这些测试」补报告命令。

**明确不在范围**：不做视频录制；不做视觉回归（像素比对）；不引入 Allure HTML 生成步骤（本报告是自包含单文件，双击即开）。

## 关联文档

- PRD：`dev_docs/ARCH_PRD/PRD-00-登录模块.md`（测试章 · 怎么跑这些测试）
- 测试文档：`dev_docs/DEV_TEST/功能测试用例/功能测试用例-登录.md`（第四节自动化归属与编号映射）
- 测试约定：`tests/AGENTS.md`（报告统一输出到 `tests/reports/`）
- 报告设计规范：`.agents/skills/html-report`（animal-island-ui 调色板、圆角、字体、阴影硬性规则）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 只改测试与报告产物，不改任何运行时行为；`.openspec.yaml` 设 `skip_specs: true`。）

## Impact

- 测试：新增 `tests/e2e/step_report.py`；修改 `tests/e2e/conftest.py`、`tests/e2e/test_login_e2e.py`。
- 产物：`tests/reports/e2e/index.html` + `tests/reports/e2e/shots/*.jpg`（`tests/reports/` 已 gitignore，可随时重新生成）。
- 依赖：Pillow 12.1.1（已装）、中文字体取自系统（msyh.ttc / simhei.ttf）。
- 前端 / 后端源码：**零改动**。
- 文档：`tests/AGENTS.md`、`dev_docs/DEV_TEST/功能测试用例/功能测试用例-登录.md`、`dev_docs/ARCH_PRD/PRD-00-登录模块.md`。
