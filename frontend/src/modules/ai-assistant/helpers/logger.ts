/**
 * Structured logger for the AI Assistant module.
 *
 * Replaces bare console.error / console.warn calls so that:
 *  - Errors always log (for production diagnostics)
 *  - Warnings only log in development (import.meta.env.DEV)
 *  - A future hook can route log entries to a remote service
 */

type LogLevel = "error" | "warn" | "info" | "debug"

interface LogEntry {
  level: LogLevel
  message: string
  detail?: unknown
  tag?: string
}

function fmt(entry: LogEntry): string {
  const prefix = entry.tag ? `[${entry.tag}] ` : ""
  return `${prefix}${entry.message}`
}

function emit(entry: LogEntry): void {
  switch (entry.level) {
    case "error":
      console.error(fmt(entry), entry.detail ?? "")
      break
    case "warn":
      if (import.meta.env.DEV) console.warn(fmt(entry), entry.detail ?? "")
      break
    case "info":
      if (import.meta.env.DEV) console.info(fmt(entry), entry.detail ?? "")
      break
    case "debug":
      if (import.meta.env.DEV) console.debug(fmt(entry), entry.detail ?? "")
      break
  }
}

/** Always-logged error. Use in catch blocks that have no user-facing notification. */
export function logError(message: string, detail?: unknown, tag?: string): void {
  emit({ level: "error", message, detail, tag })
}

/** Dev-only warning. Silently dropped in production. */
export function logWarn(message: string, detail?: unknown, tag?: string): void {
  emit({ level: "warn", message, detail, tag })
}

/** Dev-only info. */
export function logInfo(message: string, detail?: unknown, tag?: string): void {
  emit({ level: "info", message, detail, tag })
}
