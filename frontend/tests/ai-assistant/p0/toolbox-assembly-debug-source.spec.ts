import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import type { SharedToolItem } from '@/modules/ai-assistant/api/toolbox'
import {
  ASSEMBLY_SOURCES,
  buildLiveChips,
  gatedSources,
  sourceDef,
} from '@/modules/ai-assistant/helpers/toolbox-assembly'
import { useToolboxAssembly } from '@/modules/ai-assistant/composables/useToolboxAssembly'

/** 一页目录里塞满 Skill：用来证明无总闸来源不会借用这个数量当分母 */
function skillCatalog(count: number): SharedToolItem[] {
  return Array.from({ length: count }, (_, index) => ({
    id: index + 1,
    name: `skill-${index + 1}`,
    item_type: 'skill',
    enabled: true,
  }))
}

function assembly(sharedItems: SharedToolItem[] = []) {
  return useToolboxAssembly({
    platformConfig: ref({ enable_business_tools: true, enable_skills: true }),
    platformCategories: ref([]),
    platformExpanded: ref([]),
    sharedItems: ref(sharedItems),
  })
}

describe('toolbox-assembly model debug source', () => {
  it('registers the debug source as a gate-free assembly source', () => {
    const debug = ASSEMBLY_SOURCES.find((s) => s.key === 'debug')
    expect(debug).toBeTruthy()
    expect(debug?.name).toBe('模型调试')
    expect(debug?.gateKey).toBe('')
  })

  it('debug source has no master gate and never joins the live chips', () => {
    expect(gatedSources().some((s) => s.key === 'debug')).toBe(false)
    const chips = buildLiveChips({
      gates: { enable_business_tools: true, enable_skills: true },
      categories: [],
      sharedItems: skillCatalog(5),
    })
    expect(chips.some((c) => c.source === 'debug')).toBe(false)
  })

  it('describes the debug source without a gate count', () => {
    const api = assembly()
    expect(api.sourceMeta(sourceDef('debug'))).toBe('规划 / 执行 / 验收 · 仅调试不交给助手')
  })

  it('never borrows the skill catalog size as its denominator', () => {
    const api = assembly(skillCatalog(5))
    const meta = api.sourceMeta(sourceDef('debug'))
    expect(meta).not.toMatch(/\d+\s*\/\s*\d+/)
    expect(meta).not.toContain('0/5')
    expect(meta).toContain('不交给助手')
  })
})
