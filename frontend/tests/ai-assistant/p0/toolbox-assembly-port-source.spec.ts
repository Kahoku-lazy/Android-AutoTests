import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import {
  ASSEMBLY_SOURCES,
  buildLiveChips,
  gatedSources,
  sourceDef,
} from '@/modules/ai-assistant/helpers/toolbox-assembly'
import { useToolboxAssembly } from '@/modules/ai-assistant/composables/useToolboxAssembly'

function assembly() {
  return useToolboxAssembly({
    platformConfig: ref({ enable_business_tools: true, enable_skills: true }),
    platformCategories: ref([]),
    platformExpanded: ref([]),
    sharedItems: ref([]),
  })
}

describe('toolbox-assembly wireless port source', () => {
  it('registers the port source as an assembly source', () => {
    const port = ASSEMBLY_SOURCES.find((s) => s.key === 'port')
    expect(port).toBeTruthy()
    expect(port?.name).toBe('无线端口')
    expect(port?.gateKey).toBe('')
  })

  it('port source has no master gate and never joins the live chips', () => {
    expect(gatedSources().some((s) => s.key === 'port')).toBe(false)
    const chips = buildLiveChips({
      gates: { enable_business_tools: true, enable_skills: true },
      categories: [],
      sharedItems: [],
    })
    expect(chips.some((c) => c.source === 'port')).toBe(false)
  })

  it('describes the port source without a gate count', () => {
    const api = assembly()
    expect(api.sourceMeta(sourceDef('port'))).toBe('监听开关 · 原始日志 · 不交给助手')
    expect(api.sourceLiveCount(sourceDef('port'))).toBe(0)
  })

  it('no gate-free source ever shows a "n/m 生效" count', () => {
    const api = assembly()
    const gateFree = ASSEMBLY_SOURCES.filter((s) => !s.gateKey)
    expect(gateFree.length).toBeGreaterThan(0)
    for (const src of gateFree) {
      expect(api.sourceMeta(src)).not.toMatch(/\d+\s*\/\s*\d+/)
      expect(api.sourceMeta(src).length).toBeGreaterThan(0)
    }
  })
})
