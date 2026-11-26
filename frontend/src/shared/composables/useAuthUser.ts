import { ref } from "vue"
import { me } from "@/shared/api/auth"

const isSuperuser = ref(false)
const isOperator = ref(false)
const isAssistantAuthor = ref(false)
const loaded = ref(false)
let pending: Promise<void> | null = null

function load(): Promise<void> {
  if (!pending) {
    pending = me()
      .then((u) => {
        isSuperuser.value = !!u.is_superuser

        isOperator.value = u.is_operator === undefined ? !!u.is_superuser : !!u.is_operator
        isAssistantAuthor.value =
          u.is_assistant_author === undefined ? !!u.is_superuser : !!u.is_assistant_author
      })
      .catch(() => {
        isSuperuser.value = false
        isOperator.value = false
        isAssistantAuthor.value = false
      })
      .finally(() => {
        loaded.value = true
        pending = null
      })
  }
  return pending
}

export function useAuthUser() {
  if (!loaded.value) void load()
  return { isSuperuser, isOperator, isAssistantAuthor, loaded, ensure: load }
}

export function resetAuthUser(): void {
  isSuperuser.value = false
  isOperator.value = false
  isAssistantAuthor.value = false
  loaded.value = false
  pending = null
}
