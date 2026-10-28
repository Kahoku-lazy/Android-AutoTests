/**
 * 当前登录用户是否为管理员，供页面决定管理入口是否显示。
 *
 * 业务：
 * - 读取一次当前用户身份，各页面共用这一次结果
 * - 读取失败时视为非管理员
 */
import { ref } from "vue"
import { me } from "@/shared/api/auth"

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
