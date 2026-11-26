import { ref, type Ref, type ComputedRef } from "vue"
import { ElMessage } from "element-plus"

import { useLoginForm } from "@/shared/composables/useLoginForm"
import type { ViewState, FieldErrors } from "@/shared/types/auth"

import { useViewStateMachine } from "./composables/useViewStateMachine"
import { useSavedUsername } from "./composables/useSavedUsername"
import { useAuthFlow } from "./composables/useAuthFlow"

export interface LoginViewState {
  viewState: Ref<ViewState>
  loginUsername: Ref<string>
  loginPassword: Ref<string>
  rememberMe: Ref<boolean>
  regUsername: Ref<string>
  regPassword: Ref<string>
  regPassword2: Ref<string>
  regEmail: Ref<string>
  loading: Ref<boolean>
  loginErrors: ComputedRef<FieldErrors>
  canLogin: ComputedRef<boolean>
  regErrors: ComputedRef<FieldErrors>
  canRegister: ComputedRef<boolean>
  serverError: Ref<string>
  clearServerError: () => void
  handleLogin: () => Promise<void>
  handleRegister: () => Promise<void>
  switchMode: (m: ViewState) => void
}

export function useLoginView(): LoginViewState {
  const { loginUsername, rememberMe, saveUsername } = useSavedUsername()

  const loginPassword = ref("")
  const regUsername = ref("")
  const regPassword = ref("")
  const regPassword2 = ref("")
  const regEmail = ref("")

  const { loginErrors, canLogin, regErrors, canRegister } = useLoginForm(
    loginUsername,
    loginPassword,
    regUsername,
    regPassword,
    regPassword2,
    regEmail,
  )

  const { loading, serverError, clearServerError, authenticate } = useAuthFlow({ saveUsername })

  const { viewState, switchMode: baseSwitchMode } = useViewStateMachine(clearServerError)

  function switchMode(m: ViewState) {
    if (m === "register") {
      regUsername.value = ""
      regPassword.value = ""
      regPassword2.value = ""
      regEmail.value = ""
    }
    if (m === "login") {
      loginPassword.value = ""
    }
    baseSwitchMode(m)
  }

  async function handleLogin() {
    if (!canLogin.value) {
      const firstError = loginErrors.value.username || loginErrors.value.password
      ElMessage.warning(firstError || "请完善表单")
      return
    }
    await authenticate({
      mode: "login",
      username: loginUsername.value,
      password: loginPassword.value,
    })
  }

  async function handleRegister() {
    if (!canRegister.value) {
      const firstError =
        regErrors.value.username ||
        regErrors.value.email ||
        regErrors.value.password ||
        regErrors.value.password2
      ElMessage.warning(firstError || "请完善表单")
      return
    }
    await authenticate({
      mode: "register",
      username: regUsername.value,
      password: regPassword.value,
      password2: regPassword2.value,
      email: regEmail.value,
    })
  }

  return {
    viewState,
    loginUsername,
    loginPassword,
    rememberMe,
    regUsername,
    regPassword,
    regPassword2,
    regEmail,
    loading,
    loginErrors,
    canLogin,
    regErrors,
    canRegister,
    serverError,
    clearServerError,
    handleLogin,
    handleRegister,
    switchMode,
  }
}
