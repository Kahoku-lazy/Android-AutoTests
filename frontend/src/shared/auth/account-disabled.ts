/**
 * 停用账号的 10 秒退出。
 *
 * 业务：
 * 1. 识别后端专用拒绝码，不把它当成登录过期。
 * 2. 展示固定文案并倒计时，到点清空会话、回到登录页。
 * 3. 倒计时已经在走时，重复响应不重置。
 */
import {
  ACCOUNT_DISABLED_CODE,
  ACCOUNT_DISABLED_MESSAGE,
  ACCOUNT_DISABLED_SECONDS,
} from "@/shared/auth/account-disabled.constants"

let countdownStarted = false

/** 该响应是否为停用专用拒绝。 */
export function isAccountDisabled(data: unknown): boolean {
  return (
    typeof data === "object" &&
    data !== null &&
    (data as { code?: string }).code === ACCOUNT_DISABLED_CODE
  )
}

/** 开始 10 秒退出。已经在倒计时时直接返回。 */
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

/** 仅测试用：重置「已经在倒计时」标记。 */
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
