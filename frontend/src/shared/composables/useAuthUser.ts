/**
 * 当前登录用户的身份标记，供页面与侧栏决定管理入口是否显示。
 *
 * 业务：
 * - 读取一次当前用户身份（是否超管、是否运营），各页面共用这一次结果
 * - 路由守卫可以直接 await ensure() 拿结果
 * - 读取失败时按「什么都不是」处理，宁可不显示入口
 * - 登出时用 resetAuthUser() 清掉缓存，避免换账号后残留上一个人的权限
 */
import { ref } from "vue"
import { me } from "@/shared/api/auth"

const isSuperuser = ref(false)
const isOperator = ref(false)
const isAssistantAuthor = ref(false)
const loaded = ref(false)
let pending: Promise<void> | null = null

/** 拉一次身份并写进缓存；并发调用共用同一个请求。 */
function load(): Promise<void> {
  if (!pending) {
    pending = me()
      .then((u) => {
        isSuperuser.value = !!u.is_superuser
        // 老后端没有 is_operator 时退回超管口径，避免升级顺序造成入口消失
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

/** 登出或切换账号时清空缓存。 */
export function resetAuthUser(): void {
  isSuperuser.value = false
  isOperator.value = false
  isAssistantAuthor.value = false
  loaded.value = false
  pending = null
}
