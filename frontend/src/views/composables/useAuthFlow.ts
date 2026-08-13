/** useAuthFlow — 统一登录/注册 API 编排。
 *
 *  职责：调用 login/register API → 写 token → 跳转。
 *  校验逻辑在调用方（handleLogin / handleRegister）完成，
 *  本模块只处理网络层和状态副作用。
 */
import { ref, type Ref } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"

import { login, register } from "@/shared/api/auth"
import { getApiErrorMessage } from "@/shared/types/api-error"
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
  /** 统一认证入口。调用方应在调用前完成表单校验。 */
  authenticate: (params: {
    mode: "login" | "register"
    username: string
    password: string
    password2?: string
    email?: string
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
      // 登录密码不 trim（与 LoginSerializer / authenticate 一致）；注册字段与后端 strip 对齐
      const data =
        mode === "login"
          ? await login(name, password)
          : await register(name, password.trim(), password2!.trim(), email!.trim())
      if (data.status && "refresh_token" in data.data) {
        auth.loginAccount(name, data.data.access_token, data.data.refresh_token)
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
