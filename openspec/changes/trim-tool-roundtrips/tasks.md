## 1. 帧缓存与坐标核对

- [x] 1.1 新增 `engines/agents/tools/_frame_cache.py`：按 `(serial, token)` 存最近一帧的像素尺寸与截图字节，TTL 90s、每设备最多 2 帧、超限淘汰最旧；模块 docstring 按 engines 模板写全 11 字段。验证：新增单测覆盖「写入后取回」「过期取不到」「跨设备取不到」「超 2 帧淘汰最旧」
- [x] 1.2 `mark_dot` 返回体加上 `token` 与换算后的像素 `x` / `y`（`normalized=False` 时按原图像素直取），保持 `image` 字段不变。验证：`tests/engines/agents/test_tool_img_b64.py` 断言三项字段与 `x=540, y=1200`（1080×2400 屏幕、0.5/0.5）
- [x] 1.3 跑注释与风格自检：`python -m scripts.docstrings check`、`cd .agents/skills/engines-agents-style-check && python -m scripts.check_engines_agents_style`。验证：两条命令对本批改动零新增问题

## 2. 点击复用同一帧并回图

- [x] 2.1 `click_ratio` 增加可选 `token`：命中即按该帧像素坐标点击、不重新截屏；默认回传点击后页面图。验证：单测用假设备控制对象断言「截屏调用 0 次、手势 1 次、返回含 after 图与 action_time」
- [x] 2.2 `tap_screen` 同样支持 `token` 与点击后回图，`long_click` 走同一路径。验证：单测覆盖 `click` 与 `long_click` 两条路径的返回字段
- [x] 2.3 `token` 失效语义：过期或不属于该设备时返回可读 error 且**不产生任何手势**。验证：单测断言手势调用次数为 0、error 文案含「重新调用 mark_dot」
- [x] 2.4 回图可关：`shot_after=False` 时返回体不含图片字段，`action_time` 仍在。验证：单测断言 `after` 缺失且 `action_time` 存在

## 3. 执行提示词改写

- [x] 3.1 `UI_EXECUTOR_PROMPT.md` 第 2 条改为「看到红点后用核对返回的 token 直接点击，核对与点击之间不得再截图」；第 5 条 xpath 场景同样走 token；第 8 条改为「用点击工具回传的页面图复核，同一动作不截第二张」。验证：`tests/graybox/unit/test_role_prompt_guardrails.py` 新增两条断言（含「token」「不得再截图」「不得再调截图工具」关键词）
- [x] 3.2 手工通读提示词，确认没有与新规则冲突的旧表述（如「先用 screenshot_page … 再 mark_dot」）。验证：通读记录写进 tasks 勾选说明，`test_role_prompt_guardrails.py` 全绿

## 4. 日志检查增量解析

- [x] 4.1 `tool_serial._capture_rows` 改为增量：按路径缓存 `(size, mtime_ns, parsed_bytes, rows)`，只解析新增完整行，半行留待下次；`size` 变小或 `mtime_ns` 倒退时全量重解析。验证：新增单测覆盖「追加后只解析新增」「结果与全量一致」「截断回退」「轮转回退」
- [x] 4.2 把 `_local_tz()` 提到解析循环外，避免每行都取时区。验证：单测结果不变；`python -m pytest tests/engines/agents/test_tool_serial.py -q` 全绿
- [x] 4.3 用真实 8.5MB 日志做本地基准：首次全量 vs 第二次增量耗时对比。验证：`temps/` 下脚本输出「首次 ~1.5s / 第二次 <0.3s」，并贴进 `dev_docs` 分析文件

## 5. 报告与详情页耗时

- [x] 5.1 `backend/apps/task_list/task_reports.py`：轮次跨度累加 `tool_ms`（工具返回事件），步骤给出 `tool_ms` 与 `idle_ms = max(duration - model - tool, 0)`。验证：新增 api 测试断言三个字段与 clamp 0 场景
- [x] 5.2 存量任务（无工具事件）不报错，`tool_ms` / `idle_ms` 为 0。验证：api 测试用只含模型事件的任务断言字段存在且为 0
- [x] 5.3 前端步骤行展示「模型 / 工具 / 空档」三项，零值隐藏，沿用既有徽标与 `formatDurationMs`。验证：`npx vitest run` 中 `report-steps` 相关用例新增断言，覆盖「三项都显示」与「零值不显示」
- [x] 5.4 前端类型与格式：`npm run typecheck`、`npx prettier --check`。验证：两条命令通过

## 6. 验收与收尾

- [x] 6.1 本地门禁：`python run.py check`。验证：阻塞项 22/22 通过，退出码 0
- [x] 6.2 真机重跑同一份结构化定时用例（H6810），记录墙钟、`mark_dot` 次数、`screenshot_page` 次数、单次日志检查耗时。验证：墙钟低于 645s，截图次数下降，日志检查单次 < 1s；数据贴进分析文件
- [x] 6.3 更新 `dev_docs/DEV_TEST/分析-结构化任务184耗时构成-20261104.md`：补「实施后」实测对比表。验证：文件含变更前后两列数据
- [ ] 6.4 提交与推送：逐文件 `git add`、Conventional Commits、推 `Kahoku`。验证：`ci-phase1.yml` 6 个 job 全绿
