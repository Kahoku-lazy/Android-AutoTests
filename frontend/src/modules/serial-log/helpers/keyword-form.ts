/** keyword-form — 关键词表单提交前校验（纯函数，无 HTTP） */
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

/** SKU 名白名单：与后端 api._SCOPE_PATTERN 同形 */
const SKU_PATTERN = /^[A-Za-z0-9_-]+$/

export interface KeywordFormInput {
  keyword: string
  module: string
  feature: string
  scope: string
  /** 功能点编号文本；空串表示缺省（新建续编 / 编辑保持） */
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

/**
 * 表单校验：必填 / 长度 / 范围白名单 / 编号可选非负整数。
 *
 * Returns:
 *   通过时给出提交载荷（编号缺省不带字段）；失败时给出可读错误文案。
 */
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
