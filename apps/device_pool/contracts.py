"""device-pool 数据契约 — 检测/设备信息与 dp_devices 表一一对应。

纯数据层：无 I/O、无 ORM 依赖，仅定义设备状态的枚举与设备信息契约。
字段顺序与 Device 模型（dp_devices 表）保持一致，作为检测/信息阶段的类型边界。
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DeviceStatus(str, Enum):
    """设备权威状态（状态机只有两态：离线即删，无墓碑态）。"""

    ONLINE = "ONLINE"  # 在线可激活
    BUSY = "BUSY"  # 使用中（进程/观察占用）


class ConnectionType(str, Enum):
    """设备连接方式。"""

    USB = "USB"
    WIFI = "WIFI"


# 执行引擎占用前缀：强制释放/设备动作受保护，不与执行引擎抢设备（与 device_inspector 同口径）
RUNNER_OCCUPIED_PREFIXES = ("ai_agent", "runner-", "task-", "run-")


@dataclass
class DeviceInfo:
    """一台设备的完整数据契约 —— 字段与 Device 模型（dp_devices 表）一一对应。

    检测（detect）产出 serial / connection_type / connection_addr；信息（get_info）
    补全 model / brand / screen_w / screen_h / android_version；生命周期方法维护
    status / locked_* / occupied_* / connected_at / added_by；last_seen / created_at
    由 ORM 自动维护。
    """

    serial: str = ""  # 设备序列号（唯一身份，无线为真实串号）
    name: str = ""  # 设备名称
    model: str = ""  # 型号
    brand: str = ""  # 品牌
    screen_w: int = 0  # 屏幕宽度（px）
    screen_h: int = 0  # 屏幕高度（px）
    android_version: str = ""  # Android 版本（SDK int）
    connection_type: ConnectionType = ConnectionType.USB  # 连接方式：USB / WIFI
    connection_addr: str = ""  # 无线连接地址（IP:port / mDNS），USB 为空
    status: DeviceStatus = DeviceStatus.ONLINE  # 权威状态：ONLINE / BUSY
    locked_by: str = ""  # 锁定者用户 ID，空 = 公开
    locked_at: datetime | None = None  # 锁定时间
    occupied_by: str = ""  # 进程占用者（检查器 / 执行引擎）
    occupied_at: datetime | None = None  # 占用时间
    connected_at: datetime | None = None  # 首次连接时间点
    added_by: str = ""  # 添加人用户 ID
    last_seen: datetime | None = None  # 最后在线时间（ORM auto_now 维护）
    created_at: datetime | None = None  # 创建时间（ORM auto_now_add 维护）
