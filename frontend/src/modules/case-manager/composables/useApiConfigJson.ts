/**
 * useApiConfigJson — reactive config_json state for API test case editor.
 *
 * Supports two formats:
 *   single — meta / request / cases[]   (single-request data-driven)
 *   multi  — case_info / steps[] / test_data[] / validation[]
 *
 * Format is auto-detected on load via isSingleFormat() from api-config.ts.
 * meta（directory_id / priority 等）单独存放，不进 config_json。
 */
import { reactive, ref, computed, toRaw } from 'vue'
import type { ApiConfigJson, SingleApiConfig, ResolvedVariable } from '../types/api-config'
import { defaultApiConfigJson, defaultSingleApiConfig, isSingleFormat } from '../types/api-config'
import { getApiDefinition, saveApiDefinition } from '../api/apiTesting'

export interface ApiCaseMeta {
  id?: string
  priority?: string
  category?: string
  enabled?: boolean
  visibility?: string
  directory_id?: number | null
  updated_at?: string
}

function pickConfigJson(src: Record<string, any> | null | undefined): ApiConfigJson {
  const base = defaultApiConfigJson()
  if (!src || typeof src !== 'object') return base
  return {
    case_info: { ...base.case_info, ...(src.case_info || {}) },
    steps: Array.isArray(src.steps) ? src.steps : [],
    test_data: Array.isArray(src.test_data) ? src.test_data : [],
    validation: Array.isArray(src.validation) ? src.validation : [],
  }
}

function pickSingleConfig(src: Record<string, any> | null | undefined): SingleApiConfig {
  const base = defaultSingleApiConfig()
  if (!src || typeof src !== 'object') return base
  return {
    meta: { ...base.meta, ...(src.meta || {}) },
    request: { ...base.request, ...(src.request || {}) },
    cases: Array.isArray(src.cases) ? src.cases : [],
  }
}

export function useApiConfigJson(initial?: ApiConfigJson) {
  const config = reactive<ApiConfigJson>(initial ?? defaultApiConfigJson())
  const single = reactive<SingleApiConfig>(defaultSingleApiConfig())
  const meta = reactive<ApiCaseMeta>({})

  /** Current format, set explicitly during load/save. Never computed from config. */
  const format = ref<'single' | 'multi'>('multi')

  // ── Load from backend ──
  async function load(id: string) {
    const { data } = await getApiDefinition(id)
    if (!data?.status || !data.definition) {
      throw new Error(data?.message || '加载用例失败')
    }
    const def = data.definition
    const raw = def.config_json || {}

    if (isSingleFormat(raw)) {
      // ── Single format ──
      format.value = 'single'
      const next = pickSingleConfig(raw)
      Object.assign(single, next)
      // Clear multi config to avoid stale data
      Object.assign(config, defaultApiConfigJson())
    } else {
      // ── Multi format ──
      format.value = 'multi'
      const next = pickConfigJson(raw)
      if (!next.case_info.id && def.id) next.case_info.id = def.id
      if (!next.case_info.title && def.title) next.case_info.title = def.title
      if (!next.case_info.description && def.description) {
        next.case_info.description = def.description
      }
      if (!next.case_info.precondition && def.precondition) {
        next.case_info.precondition = def.precondition
      }
      Object.assign(config, next)
      // Clear single config
      Object.assign(single, defaultSingleApiConfig())
    }

    meta.id = def.id
    meta.priority = def.priority
    meta.category = def.category
    meta.enabled = def.enabled
    meta.visibility = def.visibility
    meta.directory_id = def.directory_id
    meta.updated_at = def.updated_at
  }

  // ── Save to backend ──
  async function save() {
    let config_json: Record<string, any>

    if (format.value === 'single') {
      const raw = toRaw(single)
      config_json = {
        meta: { ...raw.meta },
        request: { ...raw.request },
        cases: raw.cases.map((c) => ({
          ...c,
          input: { ...c.input, headers: { ...c.input.headers }, body: { ...c.input.body } },
          expect: { ...c.expect },
        })),
      }
    } else {
      const raw = toRaw(config)
      config_json = {
        case_info: { ...raw.case_info },
        steps: raw.steps.map((s) => ({ ...s })),
        test_data: raw.test_data.map((r) => ({ ...r })),
        validation: raw.validation.map((v) => ({ ...v })),
      }
    }

    const title = config_json.meta?.title || config_json.case_info?.title || ''
    const description = config_json.meta?.description || config_json.case_info?.description || ''

    const payload: Record<string, any> = {
      id: meta.id || undefined,
      config_json,
      title,
      description,
    }
    if (meta.priority) payload.priority = meta.priority
    if (meta.category !== undefined) payload.category = meta.category
    if (meta.directory_id != null) payload.directory_id = meta.directory_id
    if (meta.visibility) payload.visibility = meta.visibility
    if (meta.updated_at) payload.updated_at = meta.updated_at

    return saveApiDefinition(payload)
  }

  // ── Upstream variables available for step N (multi format only) ──
  function upstreamVariables(stepIndex: number): { stepIndex: number; stepName: string; name: string; path: string }[] {
    const vars: { stepIndex: number; stepName: string; name: string; path: string }[] = []
    for (let i = 0; i < stepIndex && i < config.steps.length; i++) {
      const s = config.steps[i]
      for (const ex of s.extract || []) {
        vars.push({ stepIndex: i, stepName: s.name || `步骤${i + 1}`, name: ex.name, path: ex.path })
      }
    }
    return vars
  }

  // ── Extract all {{var}} placeholders from steps → test data column headers ──
  const dataColumns = computed(() => {
    if (format.value === 'single') return []
    const cols = new Set<string>()
    const scanText = (text: string) => {
      for (const m of text.matchAll(/\{\{(\w+)\}\}/g)) {
        cols.add(m[1])
      }
    }
    for (const s of config.steps) {
      scanText(s.url || '')
      scanText(s.domain || '')
      scanText(JSON.stringify(s.headers || {}))
      scanText(JSON.stringify(s.body || {}))
      scanText(JSON.stringify(s.response_schema || {}))
    }
    for (const row of config.test_data) {
      if (row.input) {
        for (const k of Object.keys(row.input)) {
          cols.add(k)
        }
      }
    }
    return [...cols]
  })

  // ── Resolve {{var}} references in step N against upstream extracts ──
  function resolveVariables(stepIndex: number): ResolvedVariable[] {
    if (format.value === 'single') return []
    if (stepIndex >= config.steps.length) return []
    const step = config.steps[stepIndex]
    const text = JSON.stringify(step)
    const upstream = upstreamVariables(stepIndex)
    const matches = text.matchAll(/\{\{(\w+)\}\}/g)
    const seen = new Set<string>()
    return [...matches]
      .filter(m => {
        if (seen.has(m[1])) return false
        seen.add(m[1])
        return true
      })
      .map(m => ({
        name: m[1],
        resolved: upstream.find(u => u.name === m[1])
          ? {
              stepIndex: upstream.find(u => u.name === m[1])!.stepIndex,
              stepName: upstream.find(u => u.name === m[1])!.stepName,
              name: m[1],
              path: upstream.find(u => u.name === m[1])!.path,
            }
          : null,
      }))
  }

  return { config, single, meta, format, load, save, upstreamVariables, dataColumns, resolveVariables }
}
