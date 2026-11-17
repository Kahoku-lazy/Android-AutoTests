/**
 * 助手配置表单的纯数据：空白表单、由名片预填、生成提交载荷。
 *
 * 组件只渲染，字段拼装与工具勾选的形状在这里定，便于单测。
 */
import type { AssistantCard, ToolSelection } from "../types"

export interface EditorForm {
  displayName: string
  roleId: string
  domain: string
  preset: "all" | "readonly"
  removed: string[]
}

/** 新建助手时的空表单：不挂工具，与「空工具允许提交」一致。 */
export function blankForm(): EditorForm {
  return { displayName: "", roleId: "", domain: "", preset: "readonly", removed: [] }
}

/** 由名片回填：工具取第一条勾选，没有勾选就留空。 */
export function formFromCard(card: AssistantCard): EditorForm {
  const first = card.tools?.[0]
  return {
    displayName: card.display_name,
    roleId: card.role_id,
    domain: first?.domain || "",
    preset: first?.preset || "readonly",
    removed: [...(first?.remove || [])],
  }
}

/** 提交载荷里的工具勾选：没选域就是空数组（不挂工具）。 */
export function toToolSelection(form: EditorForm): ToolSelection[] {
  if (!form.domain) return []
  return [{ domain: form.domain, preset: form.preset, add: [], remove: [...form.removed] }]
}
