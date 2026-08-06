/**
 * 页面目录 — 与「元素定位 → 元素管理」同步
 */
import type { ElementDef } from '@/modules/workflow/types/workflow'
import { listPages, listPageElements, listWebGroups, listWebGroupElements } from '@/modules/workflow/api'

export type PageDomain = 'android' | 'web'

export interface CatalogPage {
  id: string
  name: string
  package?: string
  description?: string
  elements: ElementDef[]
  /** 来自 API 时为数字页 id 字符串 */
  source?: 'api' | 'mock'
  /** 页面所属域：android（App页面）或 web（Web页面） */
  domain: PageDomain
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
    domain: 'android',
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
    domain: 'android',
    elements: [
      { id: 'el_001', label: '搜索图标', type: 'icon', xpath: '//*[@content-desc="搜索"]' },
      { id: 'el_003', label: '设置按钮', type: 'button', xpath: '//*[@text="设置"]' },
    ],
  },
]

export function getMockPage(id: string): CatalogPage | undefined {
  return MOCK_PAGES.find(p => p.id === id)
}

/** 将 WebElement 映射为 ElementDef */
function mapWebElement(e: Record<string, any>): ElementDef {
  const label = e.name || e.description || `Web元素#${e.id}`
  let type = 'text'
  if (e.locator_type === 'css_selector' || e.locator_type === 'xpath') type = 'button'
  else if (e.locator_type === 'text' || e.locator_type === 'link_text') type = 'text'
  return {
    id: `web_${e.id}`,
    label: String(label),
    type,
    xpath: e.locator_value || '',
  }
}

/** 将 WebGroup 映射为 CatalogPage */
function mapWebGroup(g: Record<string, any>, elements: ElementDef[]): CatalogPage {
  return {
    id: `web_${g.id}`,
    name: g.name || `Web页面${g.id}`,
    description: `Web 页面 · ${g.element_count || elements.length} 个元素`,
    elements,
    source: 'api',
    domain: 'web',
  }
}

/** 拉取元素管理全部页面+元素（Android + Web） */
export async function fetchCatalogPages(): Promise<{
  pages: CatalogPage[]
  source: 'api' | 'mock'
  error?: string
}> {
  const pages: CatalogPage[] = []
  let source: 'api' | 'mock' = 'api'

  try {
    // Android pages
    const res = await listPages()
    const data = res.data
    if (data?.status && Array.isArray(data.pages)) {
      for (const p of data.pages) {
        if (p.is_folder) continue
        let elements: ElementDef[] = []
        try {
          const elRes = await listPageElements(p.id)
          const elData = elRes.data
          if (elData?.status && Array.isArray(elData.elements)) {
            elements = elData.elements.map(mapApiElement)
          }
        } catch { elements = [] }
        pages.push(mapApiPage(p, elements))
      }
    }
  } catch {
    source = 'mock'
  }

  // Web groups (non-folder only)
  try {
    const wRes = await listWebGroups()
    const wData = wRes.data
    if (wData?.status && Array.isArray(wData.groups)) {
      const webPages = wData.groups.filter((g: any) => !g.is_folder)
      for (const g of webPages) {
        let elements: ElementDef[] = []
        try {
          const elRes = await listWebGroupElements(g.id)
          const elData = elRes.data
          if (elData?.status && Array.isArray(elData.elements)) {
            elements = elData.elements.map(mapWebElement)
          }
        } catch { elements = [] }
        pages.push(mapWebGroup(g, elements))
      }
    }
  } catch { /* web groups optional, don't fail the whole catalog */ }

  if (pages.length === 0) {
    return { pages: MOCK_PAGES, source: 'mock', error: '无可用页面数据' }
  }
  return { pages, source }
}

/** 按页 id 重新拉取（用于「刷新关联元素」）。支持 Android (el_pages) 和 Web (el_web_groups) */
export async function fetchCatalogPageById(pageId: string): Promise<CatalogPage | null> {
  if (!pageId || pageId.startsWith('mock_')) {
    return getMockPage(pageId) || null
  }

  // Web page: id starts with "web_"
  if (pageId.startsWith('web_')) {
    const rawId = pageId.replace('web_', '')
    try {
      const wRes = await listWebGroups()
      const wData = wRes.data
      if (!wData?.status || !Array.isArray(wData.groups)) return null
      const g = wData.groups.find((x: any) => String(x.id) === String(rawId) && !x.is_folder)
      if (!g) return null
      const elRes = await listWebGroupElements(g.id)
      const elData = elRes.data
      const elements =
        elData?.status && Array.isArray(elData.elements)
          ? elData.elements.map(mapWebElement)
          : []
      return mapWebGroup(g, elements)
    } catch {
      return null
    }
  }

  // Android page
  try {
    const res = await listPages()
    const data = res.data
    if (!data?.status || !Array.isArray(data.pages)) return null
    const p = data.pages.find((x: any) => String(x.id) === String(pageId) && !x.is_folder)
    if (!p) return null
    const elRes = await listPageElements(p.id)
    const elData = elRes.data
    const elements =
      elData?.status && Array.isArray(elData.elements)
        ? elData.elements.map(mapApiElement)
        : []
    return mapApiPage(p, elements)
  } catch {
    return null
  }
}

// ── API Endpoints Catalog ──

export interface ApiEndpointRef {
  id: string
  name: string
  method: string
  url: string
  description?: string
  request_body_schema?: Record<string, any>
  response_body_schema?: Record<string, any>
}

/** 拉取 API 接口管理中的全部接口定义 */
export async function fetchApiEndpoints(): Promise<ApiEndpointRef[]> {
  try {
    const client = (await import('@/shared/api-client.js')).default
    const res = await client.get('/elements/api-endpoints')
    const data = res.data
    if (data?.status && Array.isArray(data.endpoints)) {
      return data.endpoints.map((e: any) => ({
        id: String(e.id),
        name: e.name,
        method: e.method,
        url: e.url,
        description: e.description,
        request_body_schema: e.request_body_schema || {},
        response_body_schema: e.response_body_schema || {},
      }))
    }
    return []
  } catch {
    return []
  }
}
