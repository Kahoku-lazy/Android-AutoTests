## 1. 时间从后端出来

- [x] 1.1 service 增加 `message_rows(thread)`：`role` / `content` / `created_at`（本地 ISO，带偏移）。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_assistant_threads.py -q` 断言消息带 `created_at` 且以 `+08:00` 结尾。
- [x] 1.2 日志行 `created_at` 同样输出本地 ISO 字符串（进行中的一轮为空串）。验证：日志接口测试断言字符串形态，不再回 datetime 对象。

## 2. 气泡与日志卡有时间

- [x] 2.1 前端 `ThreadMessage` 增加 `created_at`；气泡下方显示 `HH:mm`，与气泡同侧对齐，次级色 12px。验证：`cd frontend && npx vitest run tests/ai-assistant`。
- [x] 2.2 `ThreadLog` 增加 `created_at`；helper `clockLabel` 取墙上时间，`threadLogTime` 继续做编号回落。验证：`tests/ai-assistant/p0/time-label.spec.ts`。

## 3. 日志卡换成参考图样式

- [x] 3.1 一轮一张卡：`1.5px` 虚线（笔色 70% + 纸色）+ 顶部居中胶带 + `4px 4px` 硬影 + 白卡底 + **0°**；卡内时间 + 一句话结果 + 右端「查看 / 还在写」。验证：`npx vitest run tests/ai-assistant` 断言 `.thread-log__card`、`.thread-log__tape`、时间文本。
- [x] 3.2 面板退成容器（去描边），三态沿用共享件；进行中的卡不可点。验证：同一套前端测试。
- [x] 3.3 日志卡移到左栏、对话栏下面（`AssistantLanePanel` 默认插槽）；`.ai-chat__body.is-logs-open` 把左栏 `240px → clamp(320px, 30%, 420px)`，收起回 240px。验证：前端断言 `.lane-column .thread-log`、`.ai-chat__pane` 里没有日志、`is-logs-open` 类随开关增删。

## 4. 准入清单与文档同步

- [x] 4.1 `check-dashed-whitelist.mjs` OWNERS 增加 `modules/ai-assistant/components/ThreadLogPanel.vue`。验证：`node tests/check-dashed-whitelist.mjs` 通过。
- [x] 4.2 模块 `AGENTS.md` 线型条款、doodle-craft `SKILL.md` 虚线表与 `assistant-marker-card.md` §5 / §5.2 同步「第三个虚线落点 + 卡规格 + 时间戳」。验证：三处文案与代码一致，`node tests/check-style-gates.mjs` 无新增违规。

## 5. 关单

- [x] 5.1 `python manage.py check` 通过、改动文件 `ruff check` 通过；`ruff format --check` 剩余差异全在改动前既有的长行（`api.py` / `views_drf.py` / `assistant_threads.py` / `test_assistant_thread_logs.py`），本次未引入新的格式问题。
- [x] 5.2 真浏览器验收：1585×949、1280×800 两档；日志卡不倾斜、时间在；展开时左栏 383px / 320px、对话列 870px / 628px，收起回 240px；两栏网格不变形、无第二滚动条。
