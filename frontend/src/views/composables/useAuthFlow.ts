/**
 * 登录与注册的提交：发出认证请求，成功后进入工作台。
 *
 * 业务：
 * - 登录或注册成功后记下本次会话，并进入工作台
 * - 登录成功且勾选了记住账号时，留下账号名
 * - 失败时留下服务端错误文案，供登录页弹出
 * - 请求进行中处于加载中
 */
import { ref, type Ref } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"

import { login, register } from "@/shared/api/auth"
import { saveSession } from "@/shared/auth/token-storage"
import { getApiErrorMessage } from "@/shared/types/api-error"

export interface UseAuthFlowParams {
  /** 登录成功后，按「记住账号」留下或忘掉账号名 */
  saveUsername: (username: string) => void
}

export interface UseAuthFlowReturn {
  loading: Ref<boolean>
  serverError: Ref<string>
  clearServerError: () => void
  /** 提交一次登录或注册。调用前表单应已通过校验。 */
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
      // 登录密码前端不 trim：首尾空白由后端接口统一去掉，与注册侧最终口径一致。
      // 注册四个字段前端先 strip（后端同样 strip，两侧同口径）。
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
