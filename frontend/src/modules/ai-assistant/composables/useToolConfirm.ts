/** useToolConfirm — HITL 确认参数格式化 */
export function formatConfirmArgs(args: string | object): string {
  if (!args) return ''
  if (typeof args === 'string') {
    try {
      return JSON.stringify(JSON.parse(args), null, 2)
    } catch {
      return args
    }
  }
  try { return JSON.stringify(args, null, 2) } catch { return String(args) }
}
