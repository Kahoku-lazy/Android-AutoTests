/**
 * 运营后台的剪贴板写入。
 *
 * 业务：
 * 1. copyText: 复制一段纯文本，优先 Clipboard API，不可用时退回临时 textarea。
 */

/**
 * 复制一段纯文本到剪贴板。
 *
 * Clipboard API 只在安全上下文（https / localhost）可用，运营常直接走内网 IP 的 http，
 * 那里 `navigator.clipboard` 是 undefined，因此保留 textarea + execCommand 兜底。
 *
 * @param text 要复制的文本。
 * @returns 是否复制成功；调用方据此决定提示成功还是「请手动选中」。
 */
export async function copyText(text: string): Promise<boolean> {
  if (!text) return false
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {
      // 权限被拒或非安全上下文：走下面的兜底，不在这里报错
    }
  }
  const scratch = document.createElement("textarea")
  scratch.value = text
  scratch.setAttribute("readonly", "")
  scratch.setAttribute("aria-hidden", "true")
  scratch.tabIndex = -1
  scratch.style.position = "fixed"
  scratch.style.top = "0"
  scratch.style.left = "-9999px"
  scratch.style.opacity = "0"
  document.body.appendChild(scratch)
  try {
    scratch.select()
    return document.execCommand("copy")
  } catch {
    return false
  } finally {
    scratch.remove()
  }
}
