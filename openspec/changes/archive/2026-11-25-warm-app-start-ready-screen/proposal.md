## Why

启动被测 App 是几乎每个 UI 任务的第一步，而现在 `adb_app_start` 只把 `monkey` 命令打出去就返回（实测 444 ms），不告诉模型任何加载状态；模型只能连拍截图等启动页过去——退出登录那次任务为此烧掉 3 轮与 20.3K 输入 token（6,318 + 6,913 + 7,117）。

真机实测（Govee Home，R5CT62RH88F）：启动页是 `com.govee.home/.HomeActivity`（+3,084 ms），主界面是 `com.govee.home/.main.MainTabActivity`（+3,435 ms）；`dumpsys activity activities` 一次约 **125 ms**。所以「前台包名 == 目标包名」不足以保证可交互（+3 秒时已满足但还在启动页），必须等 **Activity 变化后稳定**；稳定窗口取 1200 ms，因为主 Activity 挂载后列表往往还在转圈。

## What Changes

- `adb_app_start` 增加启动就绪等待：轮询前台 Activity，直到「前台包名匹配 + Activity 变化后稳定 `settle_ms`」；超时置 `timed_out`。默认 `wait_ready=True`，可传 `False` 退回现状。
- 新增 `with_screen`：就绪后把首屏截图随结果一起返回（`ToolChunk`：JSON 元信息 + PNG），模型不必再单独发一次截图调用。
- 返回体补齐 `activity` / `activity_changes` / `waited_ms` / `polls` / `ready` / `timed_out`。
- 平台注入的运行提示补一条：启动类工具返回 `ready=true` 时最多补一张确认截图，`ready=false` 或 `timed_out` 时才按需连拍。
- 工具数量不变（仍 15 个），不新增工具。
- 非目标：不改 `adb_screenshot` / `adb_screenshot_grid` 的返回契约；不做「同 Activity 内 splash」的视觉就绪判定（这类应用退化为现有行为）；不改平台侧 `start_app`。

## 关联文档

无 PRD/ARCH 关联：本变更是引擎设备工具的入参与返回契约扩展，属工具链改动，不涉及产品需求与架构分层。

## Capabilities

### New Capabilities

- `harness-adb-app-ready`: 启动类设备工具的「就绪判定与首屏同返」契约——用什么信号判就绪、超时与稳定窗口怎么返回、首屏图怎么随结果给出，以及执行侧据此决定是否复截。

### Modified Capabilities

（无 —— 现有 `ai-device-action` 约束的是平台侧设备动作（`start_app` 等），`executor-tool-groups` 约束平台侧工具分组，`ai-screen-vision` 约束平台侧截屏，均不覆盖 `engines/ae_harness/tools/adb` 的启动工具。）

## Impact

- 代码：`engines/ae_harness/tools/adb/tools.py`（`adb_app_start`、复用 `_front_package` 与 `_screenshot_with_points`）、`engines/backend_bridge/session.py`（注入的运行提示一句话）。
- 工具目录：`build_adb_tools()` 名单不变，`list_tool_catalog()` 由构建器派生，只描述文案与参数变化。
- 产物：启动工具的返回里多出就绪字段；`with_screen=True` 时结果里多一张图，计入上下文图片数上限。
- 测试：`tests/arch/unit` 增加契约守护（默认等待、超时降级、首屏同返走同一截图实现）；另跑一次同任务 A/B 对比（轮次 / token / 墙钟）。
- 文档：`.agents/docs/engines/ae_harness_tools/ae_harness_tools_domain_tools.md` 的「启动应用」与「视觉定位精度」两处口径。
