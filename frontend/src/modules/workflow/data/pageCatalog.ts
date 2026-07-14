/**
 * 页面目录 — 与「元素定位 → 元素管理」同步
 */
import type { ElementDef } from '@/modules/workflow/types/workflow'
import { listPages, listPageElements } from '@/modules/workflow/api.js'

export interface CatalogPage {
  id: string
  name: string
  package?: string
  description?: string
  elements: ElementDef[]
  /** 来自 API 时为数字页 id 字符串 */
  source?: 'api' | 'mock'
}

/** xpath_candidates 可能是 JSON 字符串或数组 */
export function parseXpathCandidates(raw: unknown): string {
  if (!raw) return ''
  if (Array.isArray(raw)) {
    const first = raw[0]
    if (!first) return ''
    if (typeof first === 'string') return first
    return (first as { xpath?: string }).xpath || ''
  }
  if (typeof raw === 'string') {
    const t = raw.trim()
    if (!t) return ''
    if (t.startsWith('[') || t.startsWith('{')) {
      try {
        return parseXpathCandidates(JSON.parse(t))
      } catch {
        return t
      }
    }
    return t
  }
  return ''
}

function mapApiElement(e: Record<string, any>): ElementDef {
  const label =
    e.alias || e.text_val || e.content_desc || e.resource_id || `元素#${e.id}`
  let type = 'text'
  if (e.clickable) type = 'button'
  else if (e.class_name?.includes('Image')) type = 'icon'
  else if (e.class_name?.includes('Edit')) type = 'text'
  return {
    id: String(e.id),
    label: String(label),
    type,
    xpath: parseXpathCandidates(e.xpath_candidates),
  }
}

function mapApiPage(
  p: Record<string, any>,
  elements: ElementDef[]
): CatalogPage {
  return {
    id: String(p.id),
    name: p.label || `页面${p.id}`,
    package: p.package || '',
    description: p.activity || '',
    elements,
    source: 'api',
  }
}

/** Demo 回退（仅 API 失败时） */
export const MOCK_PAGES: CatalogPage[] = [
  {
    id: 'mock_home',
    name: '首页（Mock）',
    package: 'com.example.app',
    description: 'API 不可用时的示例页',
    source: 'mock',
    elements: [
      { id: 'el_001', label: '搜索图标', type: 'icon', xpath: '//*[@content-desc="搜索"]' },
      { id: 'el_003', label: '设置按钮', type: 'button', xpath: '//*[@text="设置"]' },
    ],
  },
]

export function getMockPage(id: string): CatalogPage | undefined {
  return MOCK_PAGES.find(p => p.id === id)
}

/** 拉取元素管理全部页面+元素 */
export async function fetchCatalogPages(): Promise<{
  pages: CatalogPage[]
  source: 'api' | 'mock'
  error?: string
}> {
  try {
    const res = await listPages()
    const data = res.data
    if (!data?.ok || !Array.isArray(data.pages)) {
      throw new Error(data?.error || '列表格式异常')
    }

    const pages: CatalogPage[] = []
    for (const p of data.pages) {
      if (p.is_folder) continue
      let elements: ElementDef[] = []
      try {
        const elRes = await listPageElements(p.id)
        const elData = elRes.data
        if (elData?.ok && Array.isArray(elData.elements)) {
          elements = elData.elements.map(mapApiElement)
        }
      } catch {
        elements = []
      }
      pages.push(mapApiPage(p, elements))
    }
    return { pages, source: 'api' }
  } catch (e: any) {
    const msg = e?.response?.data?.error || e?.message || '请求失败'
    return { pages: MOCK_PAGES, source: 'mock', error: String(msg) }
  }
}

/** 按页 id 重新拉取（用于「刷新关联元素」） */
export async function fetchCatalogPageById(pageId: string): Promise<CatalogPage | null> {
  if (!pageId || pageId.startsWith('mock_')) {
    return getMockPage(pageId) || null
  }
  try {
    const res = await listPages()
    const data = res.data
    if (!data?.ok || !Array.isArray(data.pages)) return null
    const p = data.pages.find((x: any) => String(x.id) === String(pageId) && !x.is_folder)
    if (!p) return null
    const elRes = await listPageElements(p.id)
    const elData = elRes.data
    const elements =
      elData?.ok && Array.isArray(elData.elements)
        ? elData.elements.map(mapApiElement)
        : []
    return mapApiPage(p, elements)
  } catch {
    return null
  }
}
