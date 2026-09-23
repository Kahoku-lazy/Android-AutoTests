/** 任务发布 — 表单状态 + 提交前校验 + 提交（multipart） */
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { listDevices, submitTask } from '../api/tasks'
import { TASK_DEVICE_POLL_INTERVAL_MS } from '../constants'
import type { DeviceRecord } from '@/shared/types/device'

export interface TaskFormState {
  title: string
  goal: string
  /** 可选附件：仅 .docx / .pdf */
  attachmentFile: File | null
  device_serial: string
}

const ATTACH_ACCEPT = '.docx,.pdf'

function emptyForm(): TaskFormState {
  return {
    title: '',
    goal: '',
    attachmentFile: null,
    device_serial: '',
  }
}

function deviceLabelOf(d: DeviceRecord): string {
  return (d.model || d.name || '').trim()
}

export function useTaskPublish() {
  const form = ref<TaskFormState>(emptyForm())
  const submitting = ref(false)
  const devices = ref<DeviceRecord[]>([])
  const dialogVisible = ref(false)

  let devicePollTimer: ReturnType<typeof setInterval> | null = null

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

  function stopDevicePoll() {
    if (devicePollTimer) {
      clearInterval(devicePollTimer)
      devicePollTimer = null
    }
  }

  function startDevicePoll() {
    stopDevicePoll()
    void loadDevices()
    devicePollTimer = setInterval(() => {
      void loadDevices()
    }, TASK_DEVICE_POLL_INTERVAL_MS)
  }

  watch(dialogVisible, (open) => {
    if (open) startDevicePoll()
    else stopDevicePoll()
  })

  onUnmounted(stopDevicePoll)

  function canSubmit(): boolean {
    return form.value.title.trim() !== '' && form.value.goal.trim() !== ''
  }

  function onAttachChange(file: File | null) {
    form.value.attachmentFile = file
  }

  function clearAttach() {
    form.value.attachmentFile = null
  }

  async function submit(onSuccess?: () => void) {
    if (!canSubmit()) {
      ElMessage.warning('请填写任务标题与任务目标')
      return
    }
    submitting.value = true
    try {
      const fd = new FormData()
      fd.append('title', form.value.title.trim())
      fd.append('goal', form.value.goal.trim())
      const serial = form.value.device_serial
      if (serial) {
        fd.append('device_serial', serial)
        const hit = devices.value.find((d) => d.serial === serial)
        const label = hit ? deviceLabelOf(hit) : ''
        if (label) fd.append('device_label', label)
      }
      if (form.value.attachmentFile) {
        fd.append('attachment', form.value.attachmentFile)
      }
      const data = await submitTask(fd)
      if (data.status) {
        ElMessage.success('任务已提交')
        form.value = emptyForm()
        onSuccess?.()
      } else {
        ElMessage.error(data.message || '提交失败')
      }
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? String((err as { response?: { data?: { message?: string } } }).response?.data?.message || '')
          : ''
      ElMessage.error(msg || '提交请求失败，请检查网络连接')
    }
    submitting.value = false
  }

  onMounted(loadDevices)

  return {
    form,
    submitting,
    devices,
    dialogVisible,
    ATTACH_ACCEPT,
    openDialog,
    closeDialog,
    canSubmit,
    submit,
    loadDevices,
    onAttachChange,
    clearAttach,
  }
}
