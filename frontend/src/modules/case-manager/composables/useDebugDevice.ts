/**
 * useDebugDevice — 调试设备选择与连接管理
 * Extracted from CaseEditor.vue
 */
import { ref, computed } from "vue";
import { ElMessage } from "element-plus";
import { listDevices, connectDebugDevice as apiConnectDebugDevice, disconnectDebugDevice as apiDisconnectDebugDevice } from "../api/uiAutomation";

export function useDebugDevice() {
  const EXEC_PREFIXES = ['runner-', 'ai_agent', 'task-', 'run-'];
  const devices = ref([]);
  const debugDevice = ref("");
  const debugConnected = ref(false);
  const debugConnecting = ref(false);

  function isExecutionOccupied(d) {
    return d.status === 'BUSY' && d.occupied_by && EXEC_PREFIXES.some(p => d.occupied_by.startsWith(p));
  }

  const availableDevices = computed(() => devices.value.filter(d => !isExecutionOccupied(d)));

  async function loadDevices() {
    try {
      const { data } = await listDevices();
      if (data.status) devices.value = data.devices || [];
    } catch { console.error("加载设备列表失败") }
  }

  async function connectDebugDevice() {
    if (!debugDevice.value) return;
    debugConnecting.value = true;
    try {
      const { data } = await apiConnectDebugDevice(debugDevice.value);
      if (data.status) {
        debugConnected.value = true;
        ElMessage.success(`已连接调试设备 ${debugDevice.value}`);
      } else {
        ElMessage.error(data.message || '连接设备失败');
      }
    } catch {
      ElMessage.error('连接设备失败');
    } finally {
      debugConnecting.value = false;
    }
  }

  function disconnectDebugDevice() {
    const serial = debugDevice.value;
    if (serial) apiDisconnectDebugDevice(serial).catch(() => {});
    debugConnected.value = false;
    debugDevice.value = '';
  }

  return { devices, debugDevice, debugConnected, debugConnecting, availableDevices, loadDevices, connectDebugDevice, disconnectDebugDevice };
}
