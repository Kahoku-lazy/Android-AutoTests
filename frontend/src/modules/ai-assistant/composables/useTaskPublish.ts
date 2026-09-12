/** 任务发布 — 表单状态 + 提交前校验 + 提交 */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listDevices, submitTask } from '../api/tasks'
import type { DeviceRecord } from '@/shared/types/device'
import type { TaskSubmitPayload } from '@/shared/types/ai'

export interface TaskFormState {
  goal: string
  attachment: string
  device_serial: string
}

function emptyForm(): TaskFormState {
  return {
    goal: '',
    attachment: '',
    device_serial: '',
  }
}

export function useTaskPublish() {
  const form = ref<TaskFormState>(emptyForm())
  const submitting = ref(false)
  const devices = ref<DeviceRecord[]>([])
  const dialogVisible = ref(false)

  function openDialog() {
    dialogVisible.value = true
  }
  function closeDialog() {
    dialogVisible.value = false
  }

  async function loadDevices() {
    try {
      const data = await listDevices()
      if (data.status && data.data) {
        devices.value = data.data.devices || []
      }
    } catch {
      // 设备列表加载失败不阻断任务提交（可留空走默认设备）
    }
  }

  function canSubmit(): boolean {
    return form.value.goal.trim() !== ''
  }

  async function submit(onSuccess?: () => void) {
    if (!canSubmit()) {
      ElMessage.warning('请填写任务目标')
      return
    }
    submitting.value = true
    try {
      const payload: TaskSubmitPayload = {
        goal: form.value.goal.trim(),
        attachment: form.value.attachment.trim(),
        device_serial: form.value.device_serial,
      }
      const data = await submitTask(payload)
      if (data.status) {
        ElMessage.success('任务已提交，正在后台执行')
        form.value = emptyForm()
        onSuccess?.()
      } else {
        ElMessage.error(data.message || '提交失败')
      }
    } catch {
      ElMessage.error('提交请求失败，请检查网络连接')
    }
    submitting.value = false
  }

  onMounted(loadDevices)

  return {
    form, submitting, devices, dialogVisible,
    openDialog, closeDialog, canSubmit, submit, loadDevices,
  }
}
