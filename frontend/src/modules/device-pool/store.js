/** device-pool Pinia store — centralized state management */
import { ref, computed } from "vue";
import { defineStore } from "pinia";
import {
  apiListDevices,
  apiScanDevices,
  apiConnectDevice,
  apiActivate,
  apiLockDevice,
  apiReleaseDevice,
  apiDisconnect,
  apiGetQueue,
  apiJoinQueue,
  apiLeaveQueue,
  apiHeartbeat,
} from "./api.js";

export const useDevicePoolStore = defineStore("device-pool", () => {
  // ── State ──
  const devices = ref([]);
  const currentSerial = ref("");
  const queueLength = ref(0);
  const queueEntries = ref([]);
  const loading = ref(false);
  const selectedSerial = ref(null);
  const scanning = ref(false);

  // ── Getters ──
  const currentDevice = computed(() =>
    devices.value.find((d) => d.serial === currentSerial.value),
  );
  const selectedDevice = computed(() =>
    devices.value.find((d) => d.serial === selectedSerial.value),
  );
  const onlineDevices = computed(() =>
    devices.value.filter((d) => d.status === "ONLINE"),
  );
  const hasDevices = computed(() => devices.value.length > 0);

  function isMyLock(device) {
    // Check if the device is locked by current user (stub — extend with auth)
    return device.locked_by && device.status === "BUSY";
  }

  // ── Actions ──

  async function fetchDevices() {
    loading.value = true;
    try {
      const { data } = await apiListDevices();
      if (data.ok) {
        devices.value = data.devices || [];
        currentSerial.value = data.current || "";
        queueLength.value = data.queue_length || 0;
      }
    } catch (_) {
      /* heartbeat failures are silent */
    }
    loading.value = false;
  }

  async function doScan(target) {
    scanning.value = true;
    try {
      const { data } = await apiScanDevices(target);
      if (data.ok) {
        devices.value = data.devices || [];
        if (data.devices?.length > 0 && !currentSerial.value) {
          currentSerial.value = data.devices[0].serial;
        }
        return data;
      }
      return data;
    } catch (e) {
      // 后端失败以 HTTP 400 返回，透传其 error 文案（AC-8）
      const data = e.response?.data;
      return data || { ok: false, error: "扫描失败" };
    } finally {
      scanning.value = false;
    }
  }

  async function doConnect(serial, opts = {}) {
    try {
      const { data } = await apiConnectDevice(serial, opts);
      if (data.ok) {
        await fetchDevices();
      }
      return data;
    } catch (e) {
      const data = e.response?.data;
      return data || { ok: false, error: "连接失败" };
    }
  }

  async function doActivate(serial) {
    try {
      const { data } = await apiActivate(serial);
      if (data.ok) {
        currentSerial.value = serial;
        await fetchDevices();
      }
      return data;
    } catch (_) {
      return { ok: false, error: "激活失败" };
    }
  }

  async function doLock(serial, userId, timeout = 300, type = "user") {
    try {
      const { data } = await apiLockDevice(serial, userId, timeout, type);
      if (data.ok) {
        await fetchDevices();
      }
      return data;
    } catch (e) {
      const data = e.response?.data;
      return data || { ok: false, error: "锁定失败" };
    }
  }

  async function doRelease(serial, opts = {}) {
    try {
      const { data } = await apiReleaseDevice(serial, opts);
      if (data.ok) {
        await fetchDevices();
      }
      return data;
    } catch (_) {
      return { ok: false, error: "释放失败" };
    }
  }

  async function doDisconnect(serial, opts = {}) {
    try {
      const { data } = await apiDisconnect(serial, opts);
      if (data.ok) {
        await fetchDevices();
      }
      return data;
    } catch (e) {
      const data = e.response?.data;
      return data || { ok: false, error: "断开失败" };
    }
  }

  async function fetchQueue() {
    try {
      const { data } = await apiGetQueue();
      if (data.ok) {
        queueEntries.value = data.queue || [];
        queueLength.value = data.count || 0;
      }
    } catch (_) {
      /* ignore */
    }
  }

  async function doJoinQueue(serial, userId) {
    try {
      const { data } = await apiJoinQueue(serial, userId);
      if (data.ok) {
        await fetchQueue();
      }
      return data;
    } catch (_) {
      return { ok: false, error: "加入排队失败" };
    }
  }

  async function doLeaveQueue(serial, userId) {
    try {
      const { data } = await apiLeaveQueue(serial, userId);
      if (data.ok) {
        await fetchQueue();
      }
      return data;
    } catch (_) {
      return { ok: false, error: "取消排队失败" };
    }
  }

  async function doHeartbeat() {
    try { await apiHeartbeat() } catch (_) { /* silent */ }
  }

  function selectDevice(serial) {
    selectedSerial.value = serial;
  }

  return {
    // state
    devices,
    currentSerial,
    queueLength,
    queueEntries,
    loading,
    selectedSerial,
    scanning,
    // getters
    currentDevice,
    selectedDevice,
    onlineDevices,
    hasDevices,
    // actions
    fetchDevices,
    doScan,
    doConnect,
    doActivate,
    doLock,
    doRelease,
    doDisconnect,
    fetchQueue,
    doJoinQueue,
    doLeaveQueue,
    doHeartbeat,
    selectDevice,
    isMyLock,
  };
});
