import { onBeforeUnmount, onMounted } from "vue"
import { onBeforeRouteLeave } from "vue-router"
import { ElMessageBox } from "element-plus"
import { useUnsavedChanges } from "@/shared/composables/useUnsavedChanges"
import {
  UNSAVED_GUARD_SKIP_PATHS,
  UNSAVED_LEAVE_CANCEL,
  UNSAVED_LEAVE_CONFIRM,
  UNSAVED_LEAVE_MESSAGE,
  UNSAVED_LEAVE_TITLE,
} from "../constants"

export async function confirmLeaveUnsaved(): Promise<boolean> {
  try {
    await ElMessageBox.confirm(UNSAVED_LEAVE_MESSAGE, UNSAVED_LEAVE_TITLE, {
      confirmButtonText: UNSAVED_LEAVE_CONFIRM,
      cancelButtonText: UNSAVED_LEAVE_CANCEL,
      type: "warning",
    })
    return true
  } catch {
    return false
  }
}

export function useUnsavedGuard(isDirty: () => boolean, isActive: () => boolean = () => true) {
  useUnsavedChanges(isDirty)

  function handleBeforeUnload(event: BeforeUnloadEvent) {
    if (!isActive()) return
    if (!isDirty()) return
    event.preventDefault()
    event.returnValue = ""
  }

  onMounted(() => {
    window.addEventListener("beforeunload", handleBeforeUnload)
  })

  onBeforeUnmount(() => {
    window.removeEventListener("beforeunload", handleBeforeUnload)
  })

  onBeforeRouteLeave(async (to) => {
    if (UNSAVED_GUARD_SKIP_PATHS.includes(to.path)) return true
    if (!isDirty()) return true
    return confirmLeaveUnsaved()
  })
}
