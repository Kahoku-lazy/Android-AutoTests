## 1. 截图与 uiautomator2 解耦（引擎驱动层）

- [x] 1.1 `engines/device/android/android_device.py`：`AndroidControl.__init__` 去掉 `u2.connect`，只保留 `super().__init__(serial)`；新增惰性 `device` 属性（首次访问才连接、缓存实例，连接失败抛带「uiautomator2 连接失败」前缀的 `RuntimeError`），`find_xpath` 与 `input_text` 改走该属性。验证：`python -m pytest tests/engines/devices/test_android_device.py -q`。**验证结果**：新增 `TestAndroidControlU2Lazy` 4 项通过；该文件 `ruff check --fix` 顺带修掉 3 处既有 lint 债（import 未排序、`adbutils.adb` 与 `serial_log` 未使用），属本任务"该文件 ruff 通过"的必要条件。
- [x] 1.2 同文件补/改测试友好点：确认 `AndroidControl(serial)` 构造不产生任何 u2 调用、截图路径（`screenshot_bytes`）不访问 `device`。验证：`python -m pytest tests/engines/devices/test_android_device.py -q` 全绿。**验证结果**：`test_construct_does_not_connect` / `test_screenshot_does_not_connect` 断言 `u2.connect` 调用次数为 0。
- [x] 1.3 新增单测（`tests/engines/devices/test_android_device.py`）：monkeypatch `u2.connect` 计数，断言「构造 = 0 次」「截图 = 0 次」「xpath 查询 = 1 次且复用不重复连接」；u2 连接抛错时 `find_xpath` 返回可读失败、截图仍成功。验证：上条命令全绿。**验证结果**：4 项通过（含 `test_u2_failure_is_readable_and_screenshot_survives`，错误文案含「uiautomator2 连接失败」）。
- [x] 1.4 回归智能体设备工具与 OCR 工具：截图仍只回 `image`、不落盘、参数只有 `serial`。验证：`python -m pytest tests/engines/agents/test_tool_device.py tests/engines/agents/test_tool_device_e2e.py tests/engines/agents/test_ocr_tool.py -q`。**验证结果**：单元 57 项通过（tool_device 51 + ocr_tool 6）；真机 e2e 6 项通过（12.79s，真机截图经 adb 成功）。

## 2. 执行角色提示词对齐现行规格

- [x] 2.1 `engines/agents/prompts/executor_prompt.py`：删除第 4、5 条中的「OCR 工具」表述，改为「归一化坐标 → xpath」两级重试口径（不再出现任何 OCR 引导）。验证：`Select-String -Path engines/agents/prompts/executor_prompt.py -Pattern 'OCR'` 无命中。**验证结果**：命中数 0。
- [x] 2.2 全仓核对提示词与工具表一致：提示词提到的工具名都可被 `select_tools` 解析，`ocr_page` 仍不在任何角色工具集。验证：`Select-String -Path engines/agents/prompts/*.py -Pattern 'ocr_page'` 无命中；`python -m pytest tests/engines/agents/test_ocr_tool.py tests/engines/agents/test_tool_device.py -q`。**验证结果**：`ocr_page` 在 prompts 命中 0；57 项通过。

## 3. 规格与文档收口

- [x] 3.1 本单 delta 覆盖 `ai-device-action` / `ai-executor-output` / `ai-verifier-output` / `ai-executor-log-check` / `ai-task-publishing` 五份能力；确认每份只改 `screenshot` 与 u2 解耦相关句子，`click_timer` / `logAssertionTimer` 等条目文字未被动过。验证：`openspec validate fix-agent-screenshot-contract --strict`。**验证结果**：`Change 'fix-agent-screenshot-contract' is valid`。
- [x] 3.2 核对 `dev_docs` 是否需要同步接口文档：本单改的是「截图不返回路径」，全仓 `dev_docs` 检索 `screenshot` / `click_timer` 无命中则记录「无需同步」，有命中则把示例字段说明改为「不采集、恒为空」。验证：递归检索 `dev_docs` 的 `click_timer|screenshot` 结果与记录一致。**验证结果**：0 命中，记录为「无需同步」。
- [x] 3.3 归档时把五份 delta 并入 `openspec/specs/`，并确认 `ai-device-action` 新增的「截图取帧不依赖 uiautomator2」进入主规格。验证：`openspec archive fix-agent-screenshot-contract` 后 `openspec validate --all`。**验证结果**：五份 delta 的 11 个 Requirement 已逐字并入主 specs（`temps/check_spec_sync.py` → `ALL_SYNCED`）；change 目录已移至 `openspec/changes/archive/2026-10-20-fix-agent-screenshot-contract`；`openspec validate --all` 90 passed / 0 failed。

## 4. 关单门禁（只跑相关面，不跑全量回归）

- [x] 4.1 后端静态门禁：`python manage.py check` + `python -m ruff check` 与 `ruff format --check` 同三文件（含新增测试）。**验证结果**：`System check identified no issues`；`ruff check` All checks passed；`ruff format --check` 3 files already formatted。
- [x] 4.2 架构边界门禁：`python tools/gen_arch_stats.py --check-boundaries`（确认解耦未引入跨模块 import 或上层直触 u2 的新依赖）。**验证结果**：模块边界检查通过，零违规（日志 `logs/boundary-check.log`）。
- [x] 4.3 真机手测：对一台 u2 服务未运行、adb 正常的设备调用 `screenshot_page(serial)`，确认返回图片且不报错；再调 `xpath_action` 确认此时才报 uiautomator2 相关错误。验证：过程日志里先有成功截图，后有 u2 相关错误。**验证结果**：R5CT62RH88F 上 `am force-stop com.github.uiautomator` 后，`screenshot_page` 仍返回 PNG（base64 1093896 字符）；随后 `xpath_action` 触发 u2 自动拉起 atx-agent 并成功返回 22 条元素（自愈），因此「连接失败」分支在真机不可复现，改由单测 `test_u2_failure_is_readable_and_screenshot_survives` 覆盖该口径。
