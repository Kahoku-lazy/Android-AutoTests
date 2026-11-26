## 1. 工具：启动就绪等待

- [x] 1.1 `adb_app_start` 增加 `wait_ready: bool = True`、`timeout_s: float = 12.0`、`settle_ms: int = 1200`；实现轮询循环：每 200 ms 读前台包名与 Activity，满足「包名匹配 + Activity 变化后稳定 settle_ms」判就绪，超时置 `timed_out`；验证：`python -m temps.check_app_ready_contract` 四项全 OK（就绪判据 / 关掉等待立即返回 / 首屏同返 / 超时降级）。
- [x] 1.2 返回体补齐 `ready` / `timed_out` / `activity` / `activity_changes` / `waited_ms` / `polls`，`wait_ready=False` 时返回形状与现状一致；验证：真机跑一次冷启动，`activity_changes` 至少两项、`ready=true`、`waited_ms` 在 3.5–6 s 量级。
- [x] 1.3 前台读取复用既有 `_front_package()`，不新增系统调用命令；验证：`adb_app_start` 源码里没有第二处 `dumpsys` 拼装。

## 2. 工具：首屏同返

- [x] 2.1 增加 `with_screen: bool = False`；为真时就绪后调用 `_screenshot_with_points(None, ...)` 返回 `ToolChunk`（JSON 元信息 + PNG），不落盘、长边压缩口径与 `adb_screenshot` 一致；验证：真机调用一次，结果为「文本 + 1 张图」，图片长边 ≤ 1024。
- [x] 2.2 返回类型注解与 docstring 同步（`ToolChunk | str`），`with_screen` 关闭时仍为纯 JSON 文本；验证：`python -m pytest -c tests/pytest.ini tests/arch/unit -q -k adb` 通过，`python -m scripts.docstrings check`（engines 技能目录）0 error。

## 3. 执行侧提示

- [x] 3.1 `engines/backend_bridge/session.py` 注入的运行提示补一句：启动类工具返回 `ready=true` 时最多补一张确认截图，`ready=false` / `timed_out` 时按需连拍；验证：真机运行时用户消息里能看到这一句，且模型在 `ready=true` 后没有再连拍。

## 4. 验证与对比

- [x] 4.1 契约守护：`tests/arch/unit` 新增断言——默认等待、超时降级不抛错、首屏同返走同一截图实现、`wait_ready=False` 分支存在；验证：`python -m pytest -c tests/pytest.ini tests/arch/unit -q` 通过（既有 5 项与本变更无关的失败在结果里注明）。
- [x] 4.2 同任务 A/B（冷启动、同角色同提示词）：改用「打开 com.govee.home → 底部我的 → 右上设置 → 停在设置页」这句状态无关的任务，四组对比（旧行为 / settle 300 / 600 / 1200）；结果：轮次 12→9、工具 11→8、首点前截图 3→0、输入 token 98,814→78,184（−21%），墙钟 24.86 s→26.72 s（+1.9 s）；验证：结果已写进 `design.md` 的「收益重算」与 `ae_harness_tools_domain_tools.md`。原句（退出登录）无法复测：首轮就把账号登出了，且用户文本里包名拼写为 `com.govee.hom`，工具如实报错未假装成功。

## 5. 文档与门禁

- [x] 5.1 更新 `.agents/docs/engines/ae_harness_tools/ae_harness_tools_domain_tools.md`：「启动应用」一节写明就绪判据、`wait_ready` / `with_screen` 与超时降级；「视觉定位精度」一节补「启动后就绪信号可替代连拍」的口径。
- [x] 5.2 门禁：`python -m ruff check` + `ruff format --check`（相关路径）、`openspec validate --strict warm-app-start-ready-screen`、`python -m utils.check_gates --only engines-agents-style`、`python -m scripts.check_engines_agents_style`（技能目录）全部通过；`python -m run check` 里 `vitest` / `vite-build` 因本机 EPERM 失败的既有情况在结果里注明。
