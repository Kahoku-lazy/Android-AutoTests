/**
 * 登录页「记住账号」：下次打开时带回上次成功登录的账号。
 *
 * 业务：
 * - 曾经记住过账号时，预填账号并勾上「记住账号」
 * - 登录成功后，勾选则留下账号，取消则忘掉
 */
import { ref, type Ref } from "vue"

const SAVED_USERNAME_KEY = "saved_username"

export interface UseSavedUsernameReturn {
  loginUsername: Ref<string>
  rememberMe: Ref<boolean>
  saveUsername: (username: string) => void
}

export function useSavedUsername(): UseSavedUsernameReturn {
  const savedUser = localStorage.getItem(SAVED_USERNAME_KEY)
  const loginUsername = ref(savedUser || "")
  const rememberMe = ref(!!savedUser)

  function saveUsername(username: string) {
    if (rememberMe.value) {
      localStorage.setItem(SAVED_USERNAME_KEY, username)
    } else {
      localStorage.removeItem(SAVED_USERNAME_KEY)
    }
  }

  return { loginUsername, rememberMe, saveUsername }
}
