/** useAuthUser — 当前登录用户身份（is_superuser），全局只拉取一次并共享。 */
import { ref } from 'vue'
import { me } from '@/shared/api/auth'

const isSuperuser = ref(false)
const loaded = ref(false)
let pending: Promise<void> | null = null

export function useAuthUser() {
  if (!loaded.value && !pending) {
    pending = me()
      .then((u) => {
        isSuperuser.value = !!u.is_superuser
      })
      .catch(() => {
        isSuperuser.value = false
      })
      .finally(() => {
        loaded.value = true
        pending = null
      })
  }
  return { isSuperuser, loaded }
}
