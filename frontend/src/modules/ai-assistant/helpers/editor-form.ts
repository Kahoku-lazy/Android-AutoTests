import type { AssistantCard, ToolSelection } from "../types"

export interface EditorForm {
  displayName: string
  roleId: string
  domain: string
  preset: "all" | "readonly"
  removed: string[]
}

export function blankForm(): EditorForm {
  return { displayName: "", roleId: "", domain: "", preset: "readonly", removed: [] }
}

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

export function toToolSelection(form: EditorForm): ToolSelection[] {
  if (!form.domain) return []
  return [{ domain: form.domain, preset: form.preset, add: [], remove: [...form.removed] }]
}
