/** toolbox-assembly — 装配台来源定义与生效清单（纯函数，无 HTTP） */
import type { PlatformToolCategory } from '../api/toolbox'
import type { SharedToolItem } from '../api/toolbox'

export type AssemblySourceKey = 'biz' | 'skill'

export interface AssemblySourceDef {
  key: AssemblySourceKey
  name: string
  desc: string
  gateKey: string
  accent: string
}

export const ASSEMBLY_SOURCES: AssemblySourceDef[] = [
  {
    key: 'biz',
    name: '平台业务',
    desc: '设备 / 用例 / 报告等平台 Tool',
    gateKey: 'enable_business_tools',
    accent: 'var(--c-device)',
  },
  {
    key: 'skill',
    name: '自定义 Skill',
    desc: 'engines/ai/skills 下的本地与上传 Skill',
    gateKey: 'enable_skills',
    accent: 'var(--c-runner)',
  },
]

export interface LiveChip {
  name: string
  source: AssemblySourceKey
  /** 业务工具所属模块 key，便于跳转展开 */
  moduleKey?: string
}

export const LIVE_CHIP_PREVIEW = 8

export function buildLiveChips(input: {
  gates: Record<string, boolean>
  categories: PlatformToolCategory[]
  sharedItems: SharedToolItem[]
}): LiveChip[] {
  const chips: LiveChip[] = []
  if (input.gates.enable_business_tools) {
    for (const cat of input.categories) {
      for (const tool of cat.tools) {
        if (tool.enabled) chips.push({ name: tool.name, source: 'biz', moduleKey: cat.key })
      }
    }
  }
  if (input.gates.enable_skills) {
    for (const item of input.sharedItems) {
      if (item.enabled && item.item_type === 'skill' && !item.missing) {
        chips.push({ name: item.name, source: 'skill' })
      }
    }
  }
  return chips
}

export function matchQuery(text: string, query: string): boolean {
  const q = query.trim().toLowerCase()
  if (!q) return true
  return text.toLowerCase().includes(q)
}
