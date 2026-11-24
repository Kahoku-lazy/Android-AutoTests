"""
模块功能：➡️ DevicePool — 设备状态管理（仅当前激活设备指针） 🏁
Python 调试：➡️ python -m backend.apps.device_pool.pool 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 device_pool 的功能用例间接覆盖，未直接 import 本模块）
🏁
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
