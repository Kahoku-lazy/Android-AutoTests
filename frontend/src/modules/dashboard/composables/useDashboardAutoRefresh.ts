/** 仪表盘统计自动刷新：页面可见时每 30 秒静默拉一次，隐藏时暂停，回来立即补一次 */
import { onMounted, onUnmounted } from "vue"

/**
 * 轮询间隔：当日费用要跟着任务推进，30 秒足够且不压后端。
 *
 * 不要再调小：统计接口本身是重查询，间隔小于单次耗时就会把请求叠起来。
 */
export const DASHBOARD_REFRESH_MS = 30_000

/**
 * 给仪表盘挂上静默轮询。
 *
 * 页面隐藏（`document.hidden`）时跳过本轮；从后台回到可见时立即刷新一次，
 * 避免用户切回来还要再等一个周期。上一轮还没返回时同样跳过本轮——
 * 慢请求叠在一起只会让后面的更慢。组件卸载时清掉定时器与监听。
 *
 * @param refresh 静默刷新函数，内部应自行吞掉错误并保留上次成功的数据。
 * @param intervalMs 轮询间隔，默认 30 秒；测试可缩短。
 */
export function useDashboardAutoRefresh(
  refresh: () => Promise<void>,
  intervalMs: number = DASHBOARD_REFRESH_MS,
): void {
  let timer: ReturnType<typeof setInterval> | null = null
  let inFlight = false

  function hidden(): boolean {
    return typeof document !== "undefined" && document.hidden
  }

  async function run(): Promise<void> {
    if (hidden() || inFlight) return
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
    timer = setInterval(() => {
      void run()
    }, intervalMs)
    document.addEventListener("visibilitychange", onVisibilityChange)
  })

  onUnmounted(() => {
    if (timer !== null) clearInterval(timer)
    timer = null
    document.removeEventListener("visibilitychange", onVisibilityChange)
  })
}
