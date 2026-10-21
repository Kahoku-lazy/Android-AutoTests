"""DevicePool — 设备状态管理（仅当前激活设备指针）。

设备连接/感知/操作的物理实现已全部下沉 engines/；本类只保留「当前激活设备」
指针。连接类型/地址直接从 Device 表读取，不再进程内缓存。
"""


class DevicePool:
    """设备状态管理 — 当前激活设备指针。"""

    current_serial = ""

    def switch_to(self, serial: str):
        """切换当前激活设备。"""
        self.current_serial = serial

    def remove_device(self, serial: str):
        """设备断开时清理当前指针。"""
        if self.current_serial == serial:
            self.current_serial = ""


device = DevicePool()
