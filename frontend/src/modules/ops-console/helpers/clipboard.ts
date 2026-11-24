export async function copyText(text: string): Promise<boolean> {
  if (!text) return false
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {}
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
