export const LOGOUT_UNSAVED_TITLE = "有改动还没有保存"

export const LOGOUT_UNSAVED_MESSAGE = "页面上的改动还没有写库，退出登录后会丢失。"

export const LOGOUT_UNSAVED_CONFIRM = "退出登录"

export const LOGOUT_UNSAVED_CANCEL = "留下"

export interface LogoutDeps {
  hasUnsaved: () => boolean
  confirmDiscard: () => Promise<boolean>
  revoke: () => Promise<unknown>
  clearSession: () => void
  goToLogin: () => void
  onRevokeError?: (error: unknown) => void
}

export async function runLogout(deps: LogoutDeps): Promise<boolean> {
  if (deps.hasUnsaved() && !(await deps.confirmDiscard())) return false
  try {
    await deps.revoke()
  } catch (error) {
    deps.onRevokeError?.(error)
  }
  deps.clearSession()
  deps.goToLogin()
  return true
}
