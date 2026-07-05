# BUG 清单 — Android-AutoTests

> 通过 30 项 Review 规则 + 文档交叉校验发现。不修改代码，仅记录。
> 日期：2026-07-02

---

## ✅ 已修复（2026-07-02）

### BUG-01 ✅：element_tools.py — SearchElementsTool 引用不存在的模型字段

- **修复**：`text`→`text_val`, `page__name`→`page__label`, `el.xpath`→`xpath_candidates` JSON 解析

### BUG-02 ✅：element_tools.py — GetTestPointsTool 引用不存在的字段

- **修复**：`el.page.name`→`el.page.label`, `el.text`→`el.text_val`

### BUG-03 ✅：Dashboard 前端调用不存在的后端 API（4 个 404）

- **修复**：新建 `apps/ai_assistant/dashboard_views.py`，在 `config/urls.py` 注册 4 个端点

### BUG-04 ✅：跨模块 service 导入（6 处全部修复）

- **修复**：全部改为 `from apps.X.api import ...`（通过 api.py 的重新导出）

### BUG-05 ✅：跨模块直接 ORM 写

- **修复**：`element_locator/views.py` 改用 `ensure_device()`

### BUG-06：VUE_API_CONTRACT.md 与实际响应不一致（2 处）

- `startTestRun()` 合同写 `{ok, run_id, ws_url}`，实际返回 `{ok, runs: [{run_id, serial}], parallel}`
- `listTestRuns()` 合同写 `runs[].run_id`，实际返回 `id`（不是 `run_id`）

### BUG-07：VUE_API_CONTRACT.md 缺少 WebSocket 消息类型（2 种）

- 未记录 `device_changed`（stream.py 发送，ScreenshotView.vue 消费）
- 未记录 `step_result`（callbacks.py 发送，test-runner/index.vue 消费）

### BUG-08：API Key 加密前的历史数据兼容性

- **文件**：`apps/ai_assistant/views.py` 中 `decrypt_key()` 对旧明文 key 有 fallback，但 `agent_factory.py` 导入 `decrypt_key` 是从 `apps.ai_assistant.views` — 如果 FastAPI 进程未初始化 Django settings，该导入会失败

### BUG-12 ✅：元素定位截图流 WebSocket HTTP 500（复发问题）

- **症状**：元素定位页左侧长期「正在连接截图流…」，画面不显示
- **根因**：`channels-redis` 默认 `msgpack` 序列化器在 Python 3.13 等环境下初始化失败 → WS 握手 500；辅以 WS 直连 `:8765` 未走代理、未激活设备、同步截图阻塞事件循环
- **修复**：`settings.py` 改 `serializer_format: 'json'`；`ScreenshotConsumer.channel_layer_alias = None`；`ws-url.js` 走 Vite 代理；设备自动 activate；`run_in_executor` 截图；`GET /api/elements/screenshot` 首帧兜底
- **文档**：详见 [元素定位截图流故障手册.md](./元素定位截图流故障手册.md)

---

## 🟢 轻微级（不影响功能但有隐患）

### BUG-09：空 skills/ 目录

- **文件**：`agentscope_service/skills/` — 目录存在但为空。AgentScope workspace 初始化引用此路径但无实际 skill 文件

### BUG-10：test_runner/views.py 误导性导入

- **文件**：`apps/test_runner/views.py:13`
- **代码**：`from .runner import _active_runs as list_active_runs` — 导入的是私有字典，别名暗示它是函数
- **影响**：`runner.py` 中存在同名的公共函数 `list_active_runs()`，两处定义冲突

### BUG-11：大量 `except Exception: pass` 吞没错误

- `apps/element_locator/stream.py:25,54,65` — WS 发送失败无日志
- `apps/device_pool/pool.py:56,132,198,207` — 设备操作失败无日志
- `apps/device_pool/views.py:37,296,404,584,659,747,850` — JSON 解析失败静默变空
- `apps/test_runner/adapter.py:76,83,97,133,184,195` — 步骤执行失败返回 False 无上下文
- `apps/element_locator/views.py:33` — 文件删除失败静默

---

## 汇总

| 严重度 | 数量 | 最紧急 |
|:--:|:--:|------|
| 🔴 阻断 | 3 | BUG-01/02 导致 AgentScope Tool 运行时崩溃 |
| 🟡 严重 | 5 | BUG-04 违反架构防火墙（6处）；BUG-05 跨模块写 |
| 🟢 轻微 | 3 | BUG-11 静默异常最多（15+处） |
| ✅ 复发已修 | 1 | BUG-12 截图流 WS 500，见专档 |
| **合计** | **12** | |
