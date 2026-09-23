import { describe, expect, it } from 'vitest'
import {
  ASSEMBLY_SOURCES,
  buildLiveChips,
  gatedSources,
} from '@/modules/ai-assistant/helpers/toolbox-assembly'

describe('toolbox-assembly device prompts source', () => {
  it('includes prompt source without gateKey', () => {
    const prompt = ASSEMBLY_SOURCES.find((s) => s.key === 'prompt')
    expect(prompt).toBeTruthy()
    expect(prompt?.gateKey).toBe('')
    expect(gatedSources().every((s) => s.gateKey)).toBe(true)
    expect(gatedSources().some((s) => s.key === 'prompt')).toBe(false)
  })

  it('live chips never include prompt items', () => {
    const chips = buildLiveChips({
      gates: { enable_business_tools: true, enable_skills: true },
      categories: [{
        key: '设备',
        icon: '📱',
        color: '#000',
        tools: [{ name: 'list_devices', summary: 'x', icon: '📱', read_only: true, enabled: true }],
      }],
      sharedItems: [{
        id: 1,
        name: 'skill-creator',
        item_type: 'skill',
        enabled: true,
      }],
    })
    expect(chips.every((c) => c.source !== 'prompt')).toBe(true)
    expect(chips.map((c) => c.name)).toEqual(['list_devices', 'skill-creator'])
  })
})
