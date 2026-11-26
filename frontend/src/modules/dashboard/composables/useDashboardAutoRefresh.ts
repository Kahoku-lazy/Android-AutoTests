import { onActivated, onDeactivated, onMounted, onUnmounted } from "vue"

export const DASHBOARD_REFRESH_MS = 30_000

export function useDashboardAutoRefresh(
  refresh: () => Promise<void>,
  intervalMs: number = DASHBOARD_REFRESH_MS,
): void {
  let timer: ReturnType<typeof setInterval> | null = null
  let inFlight = false

  let deactivated = false

  let activatedOnce = false

  function hidden(): boolean {
    return typeof document !== "undefined" && document.hidden
  }

  function clearTimer(): void {
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
  }

  function startTimer(): void {
    if (timer !== null || deactivated || intervalMs <= 0) return
    timer = setInterval(() => {
      void run()
    }, intervalMs)
  }

  async function run(): Promise<void> {
    if (hidden() || inFlight || deactivated) return
    inFlight = true
    try {
      await refresh()
    } finally {
      inFlight = false
    }
  }

  function onVisibilityChange(): void {
    void run()
  }

  onMounted(() => {
    startTimer()
    document.addEventListener("visibilitychange", onVisibilityChange)
  })

  onDeactivated(() => {
    deactivated = true
    clearTimer()
  })

  onActivated(() => {
    if (!activatedOnce) {
      activatedOnce = true
      return
    }
    deactivated = false
    startTimer()
    void run()
  })

  onUnmounted(() => {
    clearTimer()
    document.removeEventListener("visibilitychange", onVisibilityChange)
  })
}
