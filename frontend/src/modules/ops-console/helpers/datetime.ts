import {
  formatDateTime as formatDateTimeShared,
  formatRelativeTime as formatRelativeTimeShared,
} from "@/shared/helpers/datetime"

export function formatRelativeTime(value: string): string {
  return formatRelativeTimeShared(value, { granularity: "long" })
}

export function formatDateTime(value: string): string {
  return formatDateTimeShared(value, { precision: "minute" })
}
