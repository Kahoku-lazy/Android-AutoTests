/** useViewStateMachine — 登录页两态视图切换（login / register）。 */
import { ref, type Ref } from "vue"
import type { ViewState } from "@/shared/types/auth"

export interface UseViewStateMachineReturn {
  viewState: Ref<ViewState>
  switchMode: (m: ViewState) => void
}

export function useViewStateMachine(clearError: () => void): UseViewStateMachineReturn {
  const viewState = ref<ViewState>("login")

  function switchMode(m: ViewState) {
    clearError()
    viewState.value = m
  }

  return { viewState, switchMode }
}
