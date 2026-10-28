/**
 * 登录页在「登录」和「注册」之间切换。
 *
 * 业务：
 * - 打开页面时停在登录
 * - 切到另一侧时清掉当前的服务端错误提示
 */
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
