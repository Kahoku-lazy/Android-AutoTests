/** useLogPorts — 无线端口管理（列表 / 开关 / 当前日志文件读取）的 HTTP 编排
 *
 * 组件只渲染：这里负责取数、开关二次确认、日志抽屉的刷新与自动刷新定时器。
 * 日志行的合并与排序一律由服务端完成（见 helpers/log-port-lines.ts 的口径说明）。
 */
import { onBeforeUnmount, ref } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { fetchLogPortLines, fetchLogPorts, toggleLogPort } from "../api/toolbox"
import type { LogPortLine, LogPortRow } from "../api/toolbox"
import {
  LOG_AUTO_REFRESH_MS,
  LOG_DISABLE_WARNING,
  LOG_TAIL_DEFAULT,
} from "../helpers/log-port-lines"
import { formatApiError } from "@/shared/api-client"

export function useLogPorts() {
  const ports = ref<LogPortRow[]>([])
  const loading = ref(false)
  const loadError = ref("")
  const togglingPort = ref<number | null>(null)

  /** 日志抽屉 */
  const drawerVisible = ref(false)
  const activePort = ref<LogPortRow | null>(null)
  const lines = ref<LogPortLine[]>([])
  const linesLoading = ref(false)
  const conclusion = ref("")
  const note = ref("")
  const lineCount = ref(0)
  const rawLineCount = ref(0)
  const tail = ref(LOG_TAIL_DEFAULT)
  const autoRefresh = ref(false)
  let timer: ReturnType<typeof setInterval> | null = null

  async function loadPorts(): Promise<void> {
    loading.value = true
    loadError.value = ""
    try {
      const data = await fetchLogPorts()
      if (data.status) {
        ports.value = (data.data?.ports || []) as LogPortRow[]
      } else {
        loadError.value = data.message || "端口列表加载失败"
      }
    } catch (e) {
      loadError.value = formatApiError(e, "端口列表加载失败")
    } finally {
      loading.value = false
    }
  }

  /** 开关：只有人能操作；关闭前明确告知 AI 验收会降级 */
  async function setEnabled(row: LogPortRow, enabled: boolean): Promise<void> {
    if (togglingPort.value === row.port) return
    if (!enabled) {
      try {
        await ElMessageBox.confirm(LOG_DISABLE_WARNING, "关闭监听", {
          type: "warning",
          confirmButtonText: "关闭监听",
          cancelButtonText: "取消",
        })
      } catch {
        return
      }
    }
    togglingPort.value = row.port
    try {
      const data = await toggleLogPort(row.port, enabled)
      if (data.status && data.data) {
        const updated = data.data
        row.enabled = updated.enabled
        row.listening = updated.listening
        ElMessage.success(
          updated.enabled
            ? updated.listening
              ? `端口 ${row.port} 已开始监听`
              : `端口 ${row.port} 已开启，但端口未监听（可能被占用）`
            : `端口 ${row.port} 已停止监听并释放端口`,
        )
      } else {
        ElMessage.error(data.message || "操作失败")
      }
    } catch (e) {
      ElMessage.error(formatApiError(e, "操作失败"))
    } finally {
      togglingPort.value = null
    }
  }

  async function refreshLines(): Promise<void> {
    const row = activePort.value
    if (!row) return
    linesLoading.value = true
    try {
      const data = await fetchLogPortLines(row.port, tail.value)
      if (data.status && data.data) {
        const payload = data.data
        lines.value = payload.lines || []
        conclusion.value = payload.conclusion
        note.value = payload.note
        lineCount.value = payload.line_count
        rawLineCount.value = payload.raw_line_count
      } else {
        note.value = data.message || "日志读取失败"
        lines.value = []
      }
    } catch (e) {
      note.value = formatApiError(e, "日志读取失败")
      lines.value = []
    } finally {
      linesLoading.value = false
    }
  }

  function stopTimer(): void {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  function syncTimer(): void {
    stopTimer()
    if (autoRefresh.value && drawerVisible.value) {
      timer = setInterval(() => void refreshLines(), LOG_AUTO_REFRESH_MS)
    }
  }

  async function openLog(row: LogPortRow): Promise<void> {
    activePort.value = row
    drawerVisible.value = true
    await refreshLines()
    syncTimer()
  }

  function closeLog(): void {
    drawerVisible.value = false
    autoRefresh.value = false
    stopTimer()
  }

  function onAutoRefreshChange(value: boolean): void {
    autoRefresh.value = value
    syncTimer()
  }

  onBeforeUnmount(stopTimer)

  return {
    ports,
    loading,
    loadError,
    togglingPort,
    loadPorts,
    setEnabled,
    drawerVisible,
    activePort,
    lines,
    linesLoading,
    conclusion,
    note,
    lineCount,
    rawLineCount,
    tail,
    autoRefresh,
    openLog,
    closeLog,
    refreshLines,
    onAutoRefreshChange,
  }
}
