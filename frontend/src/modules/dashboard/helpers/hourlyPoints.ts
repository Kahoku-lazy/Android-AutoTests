/** 今日用量折线的点序列：逐小时 + 进行中时刻拼成 [小时, 数值] 点 */

export type HourlyPoint = [number, number]

/**
 * 第 h 小时（[h:00, h+1:00)）的点落在 h+1 时刻，语义是「到这一刻为止的那一小时用了多少」；
 * 进行中的那一小时追加到当前时刻，但只有该小时已有消耗时才追加——
 * 否则刚过整点时会在末端画出一个掉到 0 的假谷底。当前时刻不晚于最后一个点时也不重复追加。
 */
export function toHourlyPoints(
  values: (number | null)[],
  currentValue: number | null | undefined,
  currentHour: number | null | undefined,
): HourlyPoint[] {
  const points: HourlyPoint[] = []
  values.forEach((value, index) => {
    if (value === null || value === undefined) return
    points.push([index + 1, value])
  })

  if (currentHour === null || currentHour === undefined || !Number.isFinite(currentHour)) {
    return points
  }

  const last = points[points.length - 1]
  const safeCurrent = Number.isFinite(currentValue) ? (currentValue as number) : 0
  if (safeCurrent > 0 && (!last || last[0] < currentHour)) {
    points.push([currentHour, safeCurrent])
  }
  return points
}

/** 整点小时数 → `HH:00`（24 保持 24:00，不折回 00:00），用于横轴刻度 */
export function hourLabel(hour: number): string {
  const rounded = Math.round(hour)
  return `${String(rounded).padStart(2, "0")}:00`
}

/** 小时数 → `HH:MM`（含分钟，24 保持 24:00），用于 tooltip 的当前时刻 */
export function clockLabel(hour: number): string {
  const totalMinutes = Math.round(hour * 60)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`
}
