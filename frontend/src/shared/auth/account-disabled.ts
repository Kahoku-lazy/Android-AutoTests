import {
  ACCOUNT_DISABLED_CODE,
  ACCOUNT_DISABLED_MESSAGE,
  ACCOUNT_DISABLED_SECONDS,
} from "@/shared/auth/account-disabled.constants"

let countdownStarted = false

export function isAccountDisabled(data: unknown): boolean {
  return (
    typeof data === "object" &&
    data !== null &&
    (data as { code?: string }).code === ACCOUNT_DISABLED_CODE
  )
}

export function startAccountDisabledCountdown(
  clearToken: () => void,
  redirectToLogin: () => void,
): void {
  if (countdownStarted) return
  countdownStarted = true
  showNotice()
  window.setTimeout(() => {
    clearToken()
    redirectToLogin()
  }, ACCOUNT_DISABLED_SECONDS * 1000)
}

export function resetAccountDisabledCountdown(): void {
  countdownStarted = false
  document.getElementById("account-disabled-notice")?.remove()
}

function showNotice(): void {
  if (document.getElementById("account-disabled-notice")) return
  const notice = document.createElement("div")
  notice.id = "account-disabled-notice"
  notice.textContent = ACCOUNT_DISABLED_MESSAGE
  notice.setAttribute("role", "alert")
  notice.style.position = "fixed"
  notice.style.inset = "0"
  notice.style.zIndex = "var(--z-modal)"
  notice.style.display = "flex"
  notice.style.alignItems = "center"
  notice.style.justifyContent = "center"
  notice.style.background = "var(--paper)"
  notice.style.color = "var(--app-text)"
  notice.style.fontSize = "var(--app-size-md)"
  document.body.appendChild(notice)
}
