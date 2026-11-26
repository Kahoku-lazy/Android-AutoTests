import { SCOPE_GENERAL } from "./log-keyword-rows"
import {
  KEYWORD_ERR_FEATURE_ID_INVALID,
  KEYWORD_ERR_FEATURE_REQUIRED,
  KEYWORD_ERR_FEATURE_TOO_LONG,
  KEYWORD_ERR_KEYWORD_REQUIRED,
  KEYWORD_ERR_KEYWORD_TOO_LONG,
  KEYWORD_ERR_MODULE_REQUIRED,
  KEYWORD_ERR_MODULE_TOO_LONG,
  KEYWORD_ERR_SCOPE_INVALID,
} from "../constants"

const SKU_PATTERN = /^[A-Za-z0-9_-]+$/

export interface KeywordFormInput {
  keyword: string
  module: string
  feature: string
  scope: string

  featureIdText: string
}

export interface KeywordFormPayload {
  keyword: string
  module: string
  feature: string
  scope: string
  feature_id?: number
}

export type KeywordFormCheck =
  { kind: "ok"; payload: KeywordFormPayload } | { kind: "error"; error: string }

export function validateKeywordForm(input: KeywordFormInput): KeywordFormCheck {
  const keyword = (input.keyword || "").trim()
  if (!keyword) return { kind: "error", error: KEYWORD_ERR_KEYWORD_REQUIRED }
  if (keyword.length > 200) return { kind: "error", error: KEYWORD_ERR_KEYWORD_TOO_LONG }
  const module = (input.module || "").trim()
  if (!module) return { kind: "error", error: KEYWORD_ERR_MODULE_REQUIRED }
  if (module.length > 100) return { kind: "error", error: KEYWORD_ERR_MODULE_TOO_LONG }
  const feature = (input.feature || "").trim()
  if (!feature) return { kind: "error", error: KEYWORD_ERR_FEATURE_REQUIRED }
  if (feature.length > 200) return { kind: "error", error: KEYWORD_ERR_FEATURE_TOO_LONG }
  const scope = (input.scope || "").trim() || SCOPE_GENERAL
  if (scope !== SCOPE_GENERAL && !SKU_PATTERN.test(scope)) {
    return { kind: "error", error: KEYWORD_ERR_SCOPE_INVALID }
  }
  if (scope.length > 100) return { kind: "error", error: KEYWORD_ERR_SCOPE_INVALID }
  const payload: KeywordFormPayload = { keyword, module, feature, scope }
  const idText = (input.featureIdText || "").trim()
  if (idText) {
    const parsed = Number(idText)
    if (!Number.isInteger(parsed) || parsed < 0) {
      return { kind: "error", error: KEYWORD_ERR_FEATURE_ID_INVALID }
    }
    payload.feature_id = parsed
  }
  return { kind: "ok", payload }
}
