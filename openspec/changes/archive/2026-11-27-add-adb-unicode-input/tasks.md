## 1. 资产与协议层

- [x] 1.1 新增 `utils/adb_keyboard.py`：固定版本常量（URL/大小/SHA256）、`ensure_apk()` 下载校验与离线导入、`install_on()`、`ensure_ready()`、`ensure_ime()` / `restore_ime()`、`broadcast()`、`split_chunks()`、per-serial 锁，以及 `python -m utils.adb_keyboard install|status` CLI。验证：`python -c "import utils.adb_keyboard"` 通过，`python temps/verify_adb_keyboard.py` 全绿。
- [x] 1.2 写离线校验脚本 `temps/verify_adb_keyboard.py`（按 `tests/AGENTS.md` 不提交、不进 CI）：覆盖 base64 编解码、800 字符分片不拆字符、广播 `result=0` 与非 0 解析、SHA256 不匹配报错、IME 恢复在异常路径仍执行。验证：`python temps/verify_adb_keyboard.py` 全部 PASS。
- [x] 1.3 新增 `tests/arch/unit/test_adb_keyboard_parity.py`：断言工具层与 utils 两处协议的常量、编码、分片一致。验证：`python -m pytest -c tests/pytest.ini tests/arch/unit/test_adb_keyboard_parity.py` 通过（2 passed）。

## 2. 接入调用点

- [x] 2.1 新增 `engines/ae_harness/tools/adb/ime.py`（纯 adb，不读写文件、不 import `utils`）：ASCII 走原 `input text`，非 ASCII 走 IME 广播；设备未装输入法时返回失败并给出安装命令。验证：ASCII 返回结构不变；真机（已预装）输入中文成功。
- [x] 2.2 修改 `engines/device/android/android_device.py`：`AdbControl.input_text` 接入 `utils` 协议，删除 `AndroidControl.input_text` 的静默降级覆盖。验证：真机通过 `open_device(...).input.by_text("中文")` 写入成功，且 `default_input_method` 恢复原值。
- [x] 2.3 任务启动预装：`backend/apps/task_list/task_runner.py` 在 SOP 任务开始前调用 `utils.adb_keyboard.ensure_ready(serial)`，失败只告警。验证：`django.setup()` 后导入 task_runner 并调用 `ensure_ready("RF8N21MSW7A")` 返回空串，启动处已接入。

## 3. 验证与门禁

- [x] 3.1 写真机校验脚本 `temps/verify_adb_keyboard_device.py`（不提交）：先 `python -m utils.adb_keyboard install --serial RF8N21MSW7A` 预装，再打开设置搜索页、输入中文并读回断言，结束后核对输入法已恢复。验证：在 `RF8N21MSW7A` 上运行脚本输出 PASS。
- [x] 3.2 跑 `python -m run check`，阻塞项全部通过；`openspec validate add-adb-unicode-input` 通过；`engines-docstring-check` 与 `engines-agents-style-check` 无新增问题。验证：门禁 28/30 + 前端两项免沙箱直跑（96 文件 / 610 用例、构建成功）即 30/30；`openspec validate` 通过；两个风格检查 0 error / 0 violation。

## 4. 文档

- [x] 4.1 更新 `.agents/docs/engines/device/device_control_engine.md`、`.agents/docs/engines/ae_harness_tools/ae_harness_tools_domain_tools.md` 与 `engines/ae_harness/agents/README.md`：工具层与 utils 的分工、任务启动预装、CLI、IME 恢复、离线导入、GPL-2.0 与不入库约定。验证：文档描述与实现一致，链接可点。
