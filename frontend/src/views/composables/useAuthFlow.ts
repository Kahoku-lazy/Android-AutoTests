import { ref, type Ref } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"

import { login, register } from "@/shared/api/auth"
import { saveSession } from "@/shared/auth/token-storage"
import { getApiErrorMessage } from "@/shared/types/api-error"

export interface UseAuthFlowParams {
  saveUsername: (username: string) => void
}

export interface UseAuthFlowReturn {
  loading: Ref<boolean>
  serverError: Ref<string>
  clearServerError: () => void

  authenticate: (params: {
    mode: "login" | "register"
    username: string
    password: string
    password2?: string
    email?: string
  }) => Promise<void>
}

export function useAuthFlow({ saveUsername }: UseAuthFlowParams): UseAuthFlowReturn {
  const router = useRouter()
  const loading = ref(false)
  const serverError = ref("")

  function clearServerError() {
    serverError.value = ""
  }

  async function authenticate({
    mode,
    username,
    password,
    password2,
    email,
  }: {
    mode: "login" | "register"
    username: string
    password: string
    password2?: string
    email?: string
  }) {
    clearServerError()
    loading.value = true
    try {
      const name = username.trim()

      const data =
        mode === "login"
          ? await login(name, password)
          : await register(name, password.trim(), password2!.trim(), email!.trim())
      if (data.status && "refresh_token" in data.data) {
        saveSession(name, data.data.access_token, data.data.refresh_token)
        if (mode === "login") saveUsername(name)
        const successMsg = mode === "login" ? "登录成功，正在跳转..." : "注册成功，正在跳转..."
        ElMessage.success(successMsg)
        router.push("/dashboard")
      } else {
        serverError.value = data.message || (mode === "login" ? "登录失败" : "注册失败")
      }
    } catch (e: unknown) {
      serverError.value = getApiErrorMessage(e)
    } finally {
      loading.value = false
    }
  }

  return { loading, serverError, clearServerError, authenticate }
}
