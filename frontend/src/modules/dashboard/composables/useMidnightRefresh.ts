import { onMounted, onUnmounted } from "vue"

const MIDNIGHT_SETTLE_MS = 5_000

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
