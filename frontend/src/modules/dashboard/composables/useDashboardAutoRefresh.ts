/**
 * 仪表盘统计自动刷新：页面可见且仍是当前路由时每 30 秒静默拉一次，隐藏或离开页面时暂停，回来立即补一次。
 *
 * `App.vue` 用全局 keep-alive 缓存页面，切走只触发 `onDeactivated`、不触发 `onUnmounted`，
 * 所以停止条件 MUST 挂在失活上，否则仪表盘会在后台继续每 30 秒打一次统计接口。
 */
import { onActivated, onDeactivated, onMounted, onUnmounted } from "vue"

/**
 * 轮询间隔：当日费用要跟着任务推进，30 秒足够且不压后端。
 *
 * 不要再调小：统计接口本身是重查询，间隔小于单次耗时就会把请求叠起来。
 */
export const DASHBOARD_REFRESH_MS = 30_000

/**
 * 给仪表盘挂上静默轮询。
 *
 * 页面隐藏（`document.hidden`）时跳过本轮；从后台回到可见时立即刷新一次。
 * 离开仪表盘路由（keep-alive 缓存后失活）时停止定时器，重新进入时恢复并立即补一次。
 * 上一轮还没返回时同样跳过本轮——慢请求叠在一起只会让后面的更慢。
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
  /** 失活标记：keep-alive 缓存期间不跑定时器 */
  let deactivated = false
  /** `onActivated` 首次触发紧跟 `onMounted`，用它区分「首次挂载」与「从缓存回来」 */
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
    // 首次激活紧跟 onMounted，定时器已经排好，不重复启动
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
