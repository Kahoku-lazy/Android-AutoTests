/**
 * 模型名称草稿行的状态与动作：一行一个模型名。
 *
 * 实时语音 / 语音合成只维护一个模型名，所以行数在切到这两类时会收到第一行；
 * 聊天保留多行，保存时逐行建一条配置。发现模型名走 `discoverModelNames`（同一个 api 出口）。
 */
import { computed, ref, watch, type Ref } from "vue"
import { ElMessage } from "element-plus"
import { formatApiError } from "@/shared/api-client"
import { discoverModelNames } from "../api"
import type { OpsModelConfigInput } from "../types"

/** 一行一个模型名称的草稿行；key 只用于 v-for 稳定复用，不参与提交。 */
export interface NameRow {
  key: number
  value: string
}

/**
 * 组装名称草稿行。
 *
 * @param form 抽屉表单；`model_kind` 与 `base_url` 由本组合式读取。
 * @returns 行数据、加载态、提示文案与增删改查动作（名称与调用方模板一一对应）。
 */
export function useModelNameDraft(form: Ref<OpsModelConfigInput>) {
  const rows = ref<NameRow[]>([])
  const loading = ref(false)
  const hint = ref("")

  let seq = 0

  /** 新建一行并占一个稳定 key。 */
  function makeRow(value: string): NameRow {
    seq += 1
    return { key: seq, value }
  }

  /** 用给定的名称重铺草稿行；空数组时给一个空行占位。 */
  function reset(names: string[]): void {
    rows.value = (names.length ? names : [""]).map(makeRow)
  }

  function add(): void {
    rows.value.push(makeRow(""))
  }

  /** 删除一行；越界下标忽略。 */
  function remove(index: number): void {
    if (index < 0 || index >= rows.value.length) return
    rows.value.splice(index, 1)
  }

  /** 实时语音 / 语音合成的单个模型名：读取与写回第一行。 */
  const single = computed({
    get: () => rows.value[0]?.value ?? "",
    set: (value: string) => {
      if (rows.value.length) rows.value[0].value = value
      else rows.value = [makeRow(value)]
    },
  })

  /** 要提交的名称：聊天取全部非空去重行，其它类型只取第一行。 */
  function names(): string[] {
    const picked = form.value.model_kind === "chat" ? rows.value : rows.value.slice(0, 1)
    const seen: string[] = []
    for (const row of picked) {
      const name = row.value.trim()
      if (name && !seen.includes(name)) seen.push(name)
    }
    return seen
  }

  /**
   * 判断地址可用：实时语音允许 ws/wss，其余只允许 http/https。
   *
   * @param value 用户填写的地址。
   * @param kind 模型类型，缺省取当前表单值。
   * @returns 协议受支持时为 true。
   */
  function validUrl(value: string, kind = form.value.model_kind): boolean {
    const allowed = kind === "realtime" ? ["http:", "https:", "ws:", "wss:"] : ["http:", "https:"]
    try {
      return allowed.includes(new URL(value.trim()).protocol)
    } catch {
      return false
    }
  }

  /** 从当前地址拉取模型名，拉到的名字重铺成草稿行。 */
  async function discover(): Promise<void> {
    if (!validUrl(form.value.base_url)) {
      const message = form.value.base_url.trim()
        ? "API 地址必须是 http 或 https 链接"
        : "API 地址不能为空"
      hint.value = message
      ElMessage.error(message)
      return
    }
    loading.value = true
    hint.value = ""
    try {
      const { data } = await discoverModelNames(form.value)
      if (!data.status || !data.data) throw data
      const found = data.data.models || []
      if (found.length) {
        reset(found)
        hint.value = `已加载 ${found.length} 个模型，可逐行删掉不需要的`
        ElMessage.success(hint.value)
        return
      }
      hint.value = data.data.reason || "模型列表为空"
      ElMessage.warning(hint.value)
    } catch (e) {
      hint.value = formatApiError(e as never, "模型加载失败")
      ElMessage.error(hint.value)
    } finally {
      loading.value = false
    }
  }

  // 切到非聊天类型时只留第一行：那两类只维护一个模型名
  watch(
    () => form.value.model_kind,
    (kind) => {
      if (kind !== "chat" && rows.value.length > 1) rows.value = rows.value.slice(0, 1)
    },
  )

  return { rows, loading, hint, single, reset, add, remove, names, validUrl, discover }
}
