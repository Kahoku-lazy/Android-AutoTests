/**
 * Blockly/flat_steps ↔ case-manager steps_data 适配
 */
import type { Block, FlatTestStep, StepBlock, StepTypeValue } from '@/modules/workflow/types/testCase'
import { STEP_TYPE_META } from '@/modules/workflow/types/testCase'

const APP_TYPES = new Set(['start_app', 'kill_app'])

export function flattenBlocksToSteps(blocks: Block[]): FlatTestStep[] {
  const result: FlatTestStep[] = []
  function walk(list: Block[]): void {
    for (const b of list) {
      if (b.kind === 'step') {
        result.push({
          type: b.stepType,
          xpath: b.xpath,
          xpath2: b.xpath2,
          timeout: b.timeout,
          expected_text: b.expected_text,
          index: b.index,
          direction: b.direction || '',
          distance: b.distance ?? 500,
          description: b.description || b.label,
        })
      } else if (b.kind === 'branch') {
        walk(b.passChildren)
        walk(b.failChildren)
      } else if (b.kind === 'loop') {
        walk(b.children)
      }
    }
  }
  walk(blocks)
  return result
}

/** → case-manager steps_data */
export function toCaseManagerSteps(
  steps: FlatTestStep[],
  defaultPackage = ''
): Record<string, unknown>[] {
  return steps.map((s) => {
    const isApp = APP_TYPES.has(s.type)
    return {
      type: s.type,
      xpath: isApp
        ? (s.xpath || defaultPackage || '')
        : (s.xpath || ''),
      xpath2: s.xpath2 || '',
      timeout: s.timeout ?? 10,
      expected_text: s.expected_text || '',
      index: s.index ?? 0,
      direction: s.direction || '',
      distance: s.distance ?? 500,
      description: s.description || '',
    }
  })
}

/** case-manager steps_data → 线性 StepBlock[]（分支/循环平台无结构，仅平铺） */
export function fromCaseManagerSteps(steps: unknown[]): StepBlock[] {
  if (!Array.isArray(steps)) return []
  const out: StepBlock[] = []
  let i = 0
  for (const raw of steps) {
    const s = raw as Record<string, any>
    if (!s || typeof s !== 'object') continue
    const stepType = String(s.type || '')
    if (!STEP_TYPE_META[stepType]) { console.warn(`[caseBridge] Unknown step type "${stepType}" — skipping`); continue }
    const isApp = APP_TYPES.has(stepType)
    const label =
      s.description ||
      STEP_TYPE_META[stepType as StepTypeValue]?.label ||
      stepType
    out.push({
      id: `s${++i}`,
      kind: 'step',
      stepType: stepType as StepTypeValue,
      label,
      description: s.description || label,
      xpath: isApp ? '' : String(s.xpath || ''),
      xpath2: String(s.xpath2 || ''),
      timeout: Number(s.timeout) || 10,
      expected_text: String(s.expected_text || ''),
      index: Number(s.index) || 0,
      direction: String(s.direction || ''),
      distance: Number(s.distance) || 500,
      status: 'pending',
    })
  }
  return out
}

export function buildCaseSaveForm(opts: {
  id?: string
  title: string
  packageName: string
  directoryId?: number | null
  blocks: Block[]
  description?: string
  enabled?: boolean
  priority?: string
}) {
  const flat = flattenBlocksToSteps(opts.blocks)
  return {
    id: opts.id || '',
    title: opts.title.trim(),
    category: '',
    description: opts.description || '由工作流工作台 Scratch 积木同步',
    package_name: opts.packageName.trim(),
    enabled: opts.enabled !== false,
    directory_id: opts.directoryId ?? null,
    priority: opts.priority || 'P2',
    design_method: '工作流积木',
    precondition: '',
    expected_result: '',
    metrics: '',
    steps_data: toCaseManagerSteps(flat, opts.packageName),
    steps: '',
  }
}
