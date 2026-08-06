/** useAuthFlow — 统一登录/注册 API 编排。
 *
 *  将 handleLogin / handleRegister 两个 50 行重复函数合并为一个参数化流程：
 *    校验 → 清错 → loading → API 调用 → 写 token → 记住账号 → 跳转
 */
import { ref, type Ref, type ComputedRef } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"

import { login, register } from "@/shared/api/auth"
import { getApiErrorMessage } from "@/shared/types/api-error"
import type { FieldErrors } from "@/shared/types/auth"
import type { UseAuthPoolReturn } from "@/shared/composables/useAuthPool"

export interface UseAuthFlowParams {
  /** useAuthPool 返回值 */
  auth: UseAuthPoolReturn
  /** useSavedUsername 返回值 */
  saveUsername: (username: string) => void
}

export interface UseAuthFlowReturn {
  loading: Ref<boolean>
  serverError: Ref<string>
  clearServerError: () => void
  /** 统一认证入口，mode 区分登录/注册 */
  authenticate: (params: {
    mode: "login" | "register"
    username: string
    password: string
    canSubmit: ComputedRef<boolean>
    errors: ComputedRef<FieldErrors>
  }) => Promise<void>
}

export function useAuthFlow({ auth, saveUsername }: UseAuthFlowParams): UseAuthFlowReturn {
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
    canSubmit,
    errors,
  }: {
    mode: "login" | "register"
    username: string
    password: string
    password2?: string
    email?: string
    canSubmit: ComputedRef<boolean>
    errors: ComputedRef<FieldErrors>
  }) {
    if (!canSubmit.value) {
      ElMessage.warning(Object.values(errors.value)[0])
      return
    }
    clearServerError()
    loading.value = true
    try {
      const apiCall = mode === "login" ? login : register
      const data = mode === "login"
        ? await login(username.trim(), password)
        : await register(username.trim(), password, password2!, email!)
      if (data.status) {
        auth.loginAccount(username.trim(), data.access_token, data.refresh_token)
        if (mode === "login") saveUsername(username.trim())
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
