/**
 * 任务详情：运行中任务的报告自动刷新调度。
 *
 * 本模块只负责「什么时候再拉一次」，不关心报告内容：
 * 1. useReportPoll: 定时调度 + 失败退避 + 页面可见性暂停 + 卸载清理。
 *
 * 采用 `setTimeout` 自调度而非 `setInterval`：上一轮请求回来后才会排下一轮，
 * 慢响应不会堆积请求。页面隐藏期间不发请求，重新可见时立即补一次。
 */
import { onMounted, onUnmounted, ref, type Ref } from "vue"
import { REPORT_POLL_BACKOFF_MS, REPORT_POLL_MAX_FAILURES, TASK_REPORT_POLL_MS } from "../constants"

/** 自动刷新可调参数：默认取 constants 里的唯一真相源，测试按需覆盖 */
export interface ReportPollOptions {
  /** 正常间隔（毫秒）；<= 0 视为关闭自动刷新 */
  intervalMs?: number
  /** 连续失败时的退避序列，末项封顶 */
  backoffMs?: number[]
  /** 连续失败达到该次数即停止 */
  maxFailures?: number
}

/** `useReportPoll` 的返回值 */
export interface ReportPollHandle {
  /** 是否处于自动刷新中（已排下一轮或在途） */
  polling: Ref<boolean>
  /** 连续失败达到上限后为真，调用方据此提示「自动刷新已暂停」 */
  failed: Ref<boolean>
  /** 最后一次成功刷新的时刻 */
  lastUpdatedAt: Ref<Date | null>
  /** 开始轮询（首屏加载成功后调用） */
  start: () => void
  /** 立即重试一次并恢复轮询（用户手动重试时调用） */
  restart: () => void
  /** 停止轮询并清掉定时器 */
  stop: () => void
}

/**
 * 给详情页挂上报告轮询。
 *
 * Args:
 *   refresh: 拉取一次报告的函数；返回 true 表示本轮成功、false 表示失败。
 *   isActive: 是否仍需要轮询（任务未进终态）；返回 false 时停止调度。
 *   options: 间隔 / 退避序列 / 失败上限，默认取模块常量。
 *
 * Returns:
 *   轮询状态与手动控制入口。
 */
export function useReportPoll(
  refresh: () => Promise<boolean>,
  isActive: () => boolean,
  options: ReportPollOptions = {},
): ReportPollHandle {
  const intervalMs = options.intervalMs ?? TASK_REPORT_POLL_MS
  const backoffMs = options.backoffMs ?? REPORT_POLL_BACKOFF_MS
  const maxFailures = options.maxFailures ?? REPORT_POLL_MAX_FAILURES

  const polling = ref(false)
  const failed = ref(false)
  const lastUpdatedAt = ref<Date | null>(null)

  let timer: ReturnType<typeof setTimeout> | null = null
  let inFlight = false
  let stopped = true
  let failures = 0

  function hidden(): boolean {
    return typeof document !== "undefined" && document.hidden
  }

  function clearTimer(): void {
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
  }

  function stop(): void {
    stopped = true
    clearTimer()
    polling.value = false
  }

  function schedule(delay: number): void {
    clearTimer()
    if (stopped || intervalMs <= 0) {
      polling.value = false
      return
    }
    polling.value = true
    timer = setTimeout(() => {
      timer = null
      void run()
    }, delay)
  }

  async function run(): Promise<void> {
    if (inFlight) return
    if (stopped) return
    if (!isActive()) {
      stop()
      return
    }
    if (hidden()) {
      schedule(intervalMs)
      return
    }

    inFlight = true
    let ok = false
    try {
      ok = (await refresh()) === true
    } catch {
      // 请求抛错按本轮失败处理，交给退避重试
    }
    inFlight = false
    if (stopped) return

    if (ok) {
      failures = 0
      failed.value = false
      lastUpdatedAt.value = new Date()
      schedule(intervalMs)
      return
    }

    failures += 1
    if (failures > maxFailures) {
      failed.value = true
      stop()
      return
    }
    const step = Math.min(failures - 1, backoffMs.length - 1)
    schedule(backoffMs[step])
  }

  function start(): void {
    stopped = false
    failed.value = false
    failures = 0
    schedule(intervalMs)
  }

  function restart(): void {
    stopped = false
    failed.value = false
    failures = 0
    schedule(0)
  }

  /** 回到可见时补一次：正在跑就不重复排队，避免两个请求并发 */
  function onVisibilityChange(): void {
    if (hidden()) return
    if (stopped || inFlight) return
    clearTimer()
    void run()
  }

  onMounted(() => {
    document.addEventListener("visibilitychange", onVisibilityChange)
  })

  onUnmounted(() => {
    document.removeEventListener("visibilitychange", onVisibilityChange)
    stop()
  })

  return { polling, failed, lastUpdatedAt, start, restart, stop }
}
