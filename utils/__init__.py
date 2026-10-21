"""公共基础设施包。

当前内容：
1. `logs`：平台日志设施（`backend_log` / `agent_event_log` / `device_log` / `serial_log`
   四个记录器，文件轮转，串口按 SKU 与端口落盘）。

导入边界：零 `apps.*`、零 `django.*`；只依赖标准库与第三方纯库。
"""
