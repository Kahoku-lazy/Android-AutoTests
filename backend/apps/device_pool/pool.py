class DevicePool:
    current_serial = ""

    def switch_to(self, serial: str):
        self.current_serial = serial

    def remove_device(self, serial: str):
        if self.current_serial == serial:
            self.current_serial = ""


device = DevicePool()
