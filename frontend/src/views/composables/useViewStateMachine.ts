/** useViewStateMachine — 登录页三态视图切换。 */
import { ref, onMounted, type Ref, type ComputedRef } from "vue"
import { useRouter, useRoute } from "vue-router"
import type { ViewState } from "@/shared/types/auth"

export interface UseViewStateMachineReturn {
  viewState: Ref<ViewState>
  switchMode: (m: ViewState) => void
  onSwitchToExisting: () => void
  onAddNewAccount: () => void
}

export function useViewStateMachine(
  accountList: ComputedRef<string[]>,
  clearError: () => void,
): UseViewStateMachineReturn {
  const router = useRouter()
  const route = useRoute()

  const viewState = ref<ViewState>("login")

  onMounted(() => {
    if (accountList.value.length > 0 && !route.query.add) {
      viewState.value = "switchPrompt"
    }
  })

  function switchMode(m: ViewState) {
    clearError()
    viewState.value = m
  }

  function onSwitchToExisting() {
    router.push("/dashboard")
  }

  function onAddNewAccount() {
    clearError()
    viewState.value = "login"
    router.replace({ query: { add: "1" } })
  }

  return { viewState, switchMode, onSwitchToExisting, onAddNewAccount }
}
