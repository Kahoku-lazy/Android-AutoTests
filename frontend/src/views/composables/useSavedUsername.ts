/** useSavedUsername — 记住账号 localStorage 读写。 */
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
