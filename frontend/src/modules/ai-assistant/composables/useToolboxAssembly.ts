/** useToolboxAssembly — 装配台 UI 状态（来源切换 / 生效芯片 / 搜索 / 跳转） */
import { computed, nextTick, ref, watch, type Ref } from 'vue'
import type { PlatformToolCategory, PlatformToolItem, SharedToolItem } from '../api/toolbox'
import {
  ASSEMBLY_SOURCES,
  LIVE_CHIP_PREVIEW,
  buildLiveChips,
  matchQuery,
  type AssemblySourceDef,
  type AssemblySourceKey,
  type LiveChip,
} from '../helpers/toolbox-assembly'

export function useToolboxAssembly(deps: {
  platformConfig: Ref<Record<string, unknown>>
  platformCategories: Ref<PlatformToolCategory[]>
  platformExpanded: Ref<string[]>
  sharedItems: Ref<SharedToolItem[]>
}) {
  const activeSource = ref<AssemblySourceKey>('biz')
  const searchQuery = ref('')
  const chipsExpanded = ref(false)
  const highlightName = ref('')
  let highlightTimer: ReturnType<typeof setTimeout> | null = null

  const activeSourceDef = computed(
    () => ASSEMBLY_SOURCES.find((s) => s.key === activeSource.value) || ASSEMBLY_SOURCES[0],
  )

  function isGateOn(gateKey: string): boolean {
    return Boolean(deps.platformConfig.value[gateKey])
  }

  const liveChips = computed(() => buildLiveChips({
    gates: {
      enable_business_tools: isGateOn('enable_business_tools'),
      enable_skills: isGateOn('enable_skills'),
    },
    categories: deps.platformCategories.value,
    sharedItems: deps.sharedItems.value,
  }))

  const visibleChips = computed(() => (
    chipsExpanded.value ? liveChips.value : liveChips.value.slice(0, LIVE_CHIP_PREVIEW)
  ))

  const unarmedSources = computed(() => ASSEMBLY_SOURCES.filter((s) => !isGateOn(s.gateKey)))

  function sourceLiveCount(src: AssemblySourceDef): number {
    if (!isGateOn(src.gateKey)) return 0
    return liveChips.value.filter((c) => c.source === src.key).length
  }

  function sourceCatalogTotal(src: AssemblySourceDef): number {
    if (src.key === 'biz') {
      return deps.platformCategories.value.reduce((n, c) => n + c.tools.length, 0)
    }
    return deps.sharedItems.value.filter((i) => i.item_type === 'skill').length
  }

  function sourceMeta(src: AssemblySourceDef): string {
    if (!isGateOn(src.gateKey)) return '总闸关闭 · 目录启停不会进入运行时'
    return `${sourceLiveCount(src)}/${sourceCatalogTotal(src)} 生效`
  }

  function toolDomId(source: string, name: string) {
    return `tb-tool-${source}-${encodeURIComponent(name)}`
  }

  async function jumpToChip(chip: LiveChip) {
    activeSource.value = chip.source
    if (chip.source === 'biz' && chip.moduleKey) {
      if (!deps.platformExpanded.value.includes(chip.moduleKey)) {
        deps.platformExpanded.value = [...deps.platformExpanded.value, chip.moduleKey]
      }
    }
    highlightName.value = chip.name
    if (highlightTimer) clearTimeout(highlightTimer)
    highlightTimer = setTimeout(() => { highlightName.value = '' }, 1400)
    await nextTick()
    document.getElementById(toolDomId(chip.source, chip.name))
      ?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }

  function filterTools(tools: PlatformToolItem[]) {
    return tools.filter((t) => matchQuery(`${t.name} ${t.summary}`, searchQuery.value))
  }

  const filteredCategories = computed(() => {
    const q = searchQuery.value.trim()
    if (!q) return deps.platformCategories.value
    return deps.platformCategories.value.filter((cat) => filterTools(cat.tools).length > 0)
  })

  const filteredSkillItems = computed(() => (
    deps.sharedItems.value.filter((i) => (
      i.item_type === 'skill'
      && matchQuery(`${i.name} ${i.description || ''}`, searchQuery.value)
    ))
  ))

  watch(searchQuery, (q) => {
    if (!q.trim() || activeSource.value !== 'biz') return
    const keys = filteredCategories.value.map((c) => c.key)
    deps.platformExpanded.value = Array.from(new Set([...deps.platformExpanded.value, ...keys]))
  })

  return {
    ASSEMBLY_SOURCES,
    LIVE_CHIP_PREVIEW,
    activeSource,
    activeSourceDef,
    searchQuery,
    chipsExpanded,
    highlightName,
    liveChips,
    visibleChips,
    unarmedSources,
    isGateOn,
    sourceLiveCount,
    sourceMeta,
    toolDomId,
    jumpToChip,
    filterTools,
    filteredCategories,
    filteredSkillItems,
  }
}
