/** useModelDebugFolding — 模型调试页的折叠态（思考过程逐条独立 / 工具分组逐组独立，切角色重置） */
import { ref, watch } from "vue"
import type { Ref } from "vue"

export function useModelDebugFolding(role: Ref<string>) {
  /** 思考过程默认展开：只记「被收起」的消息 id，因此折叠态逐条独立 */
  const thinkingCollapsed = ref<number[]>([])

  /** 工具分组展开态：只记「已展开」的分类（白名单），因此默认全部收起 */
  const openToolGroups = ref<string[]>([])

  /** 清空折叠态（切角色与清空对话共用，避免残留 id / 分类名） */
  function reset(): void {
    thinkingCollapsed.value = []
    openToolGroups.value = []
  }

  watch(role, reset)

  function thinkingOf(item: { thinking?: string[] }): string {
    return (item.thinking || []).join("\n\n")
  }

  /** 思考过程字数（与展示文本同口径） */
  function thinkingCharsOf(item: { thinking?: string[] }): number {
    return thinkingOf(item).length
  }

  function isThinkingOpen(id: number): boolean {
    return !thinkingCollapsed.value.includes(id)
  }

  function toggleThinking(id: number): void {
    thinkingCollapsed.value = isThinkingOpen(id)
      ? [...thinkingCollapsed.value, id]
      : thinkingCollapsed.value.filter((item) => item !== id)
  }

  function isToolGroupOpen(category: string): boolean {
    return openToolGroups.value.includes(category)
  }

  /** 工具分组逐组独立开合：展开项按分类名记在 openToolGroups 里 */
  function toggleToolGroup(category: string): void {
    openToolGroups.value = isToolGroupOpen(category)
      ? openToolGroups.value.filter((item) => item !== category)
      : [...openToolGroups.value, category]
  }

  return {
    thinkingCollapsed,
    openToolGroups,
    reset,
    thinkingOf,
    thinkingCharsOf,
    isThinkingOpen,
    toggleThinking,
    isToolGroupOpen,
    toggleToolGroup,
  }
}
