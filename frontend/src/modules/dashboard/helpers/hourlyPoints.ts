export type HourlyPoint = [number, number]

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

export function hourLabel(hour: number): string {
  const rounded = Math.round(hour)
  return `${String(rounded).padStart(2, "0")}:00`
}

export function clockLabel(hour: number): string {
  const totalMinutes = Math.round(hour * 60)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`
}
