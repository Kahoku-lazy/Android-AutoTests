/** 跨零点自动换天：本地日期变化后触发一次刷新并重新排期 */
import { onMounted, onUnmounted } from "vue"

/** 零点后再等 5 秒，避开边界上的服务端时钟差 */
const MIDNIGHT_SETTLE_MS = 5_000

/** 距下一个本地 00:00:05 的毫秒数（至少 1 秒，避免负数定时器） */
export function msUntilNextMidnight(now: Date = new Date()): number {
  const nextMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 0, 0)
  return Math.max(1000, nextMidnight.getTime() - now.getTime() + MIDNIGHT_SETTLE_MS)
}

export function useMidnightRefresh(onRollover: () => void): void {
  let timer: ReturnType<typeof setTimeout> | null = null

  function schedule(): void {
    timer = setTimeout(() => {
      onRollover()
      schedule()
    }, msUntilNextMidnight())
  }

  onMounted(schedule)

  onUnmounted(() => {
    if (timer !== null) clearTimeout(timer)
    timer = null
  })
}
