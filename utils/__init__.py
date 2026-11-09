"""公共基础设施包。

当前内容：
1. `logs`：平台日志设施（`backend_log` / `agent_event_log` / `device_log` / `serial_log`
   四个记录器，文件轮转，串口按 SKU 与端口落盘）——**库**，供业务代码 import。
2. `adb`：adb 可执行文件解析（平台自带优先，不回退系统 PATH）——**库**，供 backend / engines 使用。
3. `platform_tools`：platform-tools 安装器（`python run.py setup` 调用）——库 + CLI。
4. `check_gates` · `gen_arch_stats` · `check_openapi_coverage` · `live_screen`：开发与门禁
   脚本——**只供 CLI 调用**（`python utils/xxx.py`），业务代码**不得** import。
5. `boundary-whitelist.json` · `frontend-whitelist.json`：上述脚本读取的白名单数据，
   路径由脚本内 `PROJECT_ROOT / "utils"` 定位。

导入边界：零 `apps.*`、零 `django.*`；只依赖标准库与第三方纯库。包本身保持零 import、
零副作用——`import utils` 不会拉起任何脚本的副作用（脚本只在 `__main__` 里执行）。
"""
