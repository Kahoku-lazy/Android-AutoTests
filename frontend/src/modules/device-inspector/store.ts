/** device-inspector Pinia store — v1.7 快照中心：设备列表 / capture / 快照回看删除 / 保存到元素定位 / 页面回看 */
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import {
  apiCapture,
  apiGetSnapshots,
  apiGetSnapshot,
  apiDeleteSnapshot,
  apiAnalyzeSnapshot,
  apiSaveToElements,
  apiGetPageView,
  apiGetDevices,
} from './api'
import { matchOcrToElements } from '@/shared/ocrMatch'

// 执行引擎占用前缀：不可用于 capture（PRD-03 §4.1）
const EXEC_PREFIXES = ['runner-', 'ai_agent', 'task-', 'run-']

function isExecutionOccupied(device) {
  return device.status === 'BUSY' && device.occupied_by &&
    EXEC_PREFIXES.some(p => device.occupied_by.startsWith(p))
}

const INPUT_CLASS_KEYWORDS = ['edittext', 'autocomplete', 'searchview']

function isInputClass(className) {
  if (!className) return false
  const c = className.toLowerCase()
  return INPUT_CLASS_KEYWORDS.some(k => c.includes(k))
}

/** 缩略图 / 截图相对路径 → 媒体 URL */
export function mediaUrl(path) {
  if (!path) return ''
  return `/media/${path}`
}

export const useElementStore = defineStore('device-inspector', () => {
  // ── Device ──
  const devices = ref([])
  const captureSerial = ref('')
  const captureMethod = ref('both') // 'dump' | 'ocr' | 'both'

  const availableDevices = computed(() =>
    devices.value.filter(d =>
      (d.status === 'ONLINE' || d.status === 'BUSY') && !isExecutionOccupied(d)
    )
  )

  // ── Snapshot state ──
  const snapshot = ref(null)      // 当前展示的快照全量 JSON
  const snapshots = ref([])       // 快照列表 items
  const snapshotTotal = ref(0)
  const captLoading = ref(false)
  const error = ref('')

  // ── 展示（合并表格：dump 元素 + OCR 文本，_kind 区分）──
  const elements = computed(() => snapshot.value?.elements || [])
  const ocrTexts = computed(() => snapshot.value?.texts || [])
  const selected = ref(null)      // 选中元素（截图联动）
  const selectedOcr = ref(null)
  const filterMode = ref('all')
  const searchText = ref('')
  const nameOverrides = ref<Record<string, string>>({})   // { [元素 _idx]: 自定义元素名称 }（结构分析表内联重命名）

  // ── 结构分析（纯规则分区，后端即时计算不落库）──
  const analysis = ref(null)      // {is_webview, sections, elements}
  const analyzing = ref(false)
  const viewMode = ref('elements') // 'elements' | 'structure'

  /**
   * 合并行：按「中心点包含 + 最小面积」把 OCR 文本合并进 dump 元素行——
   * 匹配行 _kind='dump' + _ocrMatched=true（附 ocr_text/ocr_confidence/ocr_thumbnail_path）；
   * 未匹配的 OCR 独立成行（_kind='ocr'，_rowKey='o{idx}'）。口径见 shared/ocrMatch.ts。
   */
  const mergedRows = computed(() => {
    const { byElement, matchedOcrIndexes } = matchOcrToElements(elements.value, ocrTexts.value)
    const rows = elements.value.map((e, i) => {
      const base = { ...e, _kind: 'dump', _rowKey: `d${e._idx ?? e.__uid}` }
      const match = byElement.get(i)
      if (match) {
        return {
          ...base,
          _ocrMatched: true,
          ocr_text: match.text,
          ocr_confidence: match.confidence,
          ocr_thumbnail_path: match.thumbnail_path,
          ocr_idx: match._idx,
        }
      }
      return base
    })
    const unmatched = ocrTexts.value
      .filter((t, i) => !matchedOcrIndexes.has(i))
      .map(t => ({ ...t, _kind: 'ocr', _rowKey: `o${t._idx ?? t.__uid}` }))
    return [...rows, ...unmatched]
  })

  const filteredElements = computed(() => {
    let els = elements.value || []
    switch (filterMode.value) {
      case 'clickable': els = els.filter(e => e.clickable); break
      case 'text': els = els.filter(e => e.text); break
      case 'rid': els = els.filter(e => e.resource_id); break
      case 'clickable_text': els = els.filter(e => e.clickable && e.text); break
      case 'clickable_no_text': els = els.filter(e => e.clickable && !e.text); break
      case 'input': els = els.filter(e => isInputClass(e.class_name)); break
      case 'scrollable': els = els.filter(e => e.scrollable); break
    }
    const q = searchText.value.trim().toLowerCase()
    if (q) {
      els = els.filter(e =>
        (e.text || '').toLowerCase().includes(q) ||
        (e.resource_id || '').toLowerCase().includes(q) ||
        (e.content_desc || '').toLowerCase().includes(q) ||
        (e.class_name || '').toLowerCase().includes(q)
      )
    }
    return els
  })

  /** 合并表格行：筛选模式作用于 dump 行（非 all 时隐藏纯 OCR 行），搜索对两类都生效 */
  const filteredRows = computed(() => {
    const q = searchText.value.trim().toLowerCase()
    const elKeys = new Set(filteredElements.value.map(e => `d${e._idx ?? e.__uid}`))
    return mergedRows.value.filter(row => {
      if (row._kind === 'ocr' && filterMode.value !== 'all') return false
      if (row._kind === 'dump' && !elKeys.has(row._rowKey)) return false
      if (q) {
        const hay = `${row.text || ''} ${row.ocr_text || ''} ${row.resource_id || ''} ${row.content_desc || ''} ${row.class_name || ''}`.toLowerCase()
        if (!hay.includes(q)) return false
      }
      return true
    })
  })

  // ── 勾选（保存到元素定位的筛减；key = _rowKey）──
  const checkedIds = ref(new Set())
  function toggleCheck(row) {
    if (!row || typeof row !== 'object') return
    const id = row._rowKey ?? row._idx ?? row.__uid
    if (id == null) return
    const next = new Set(checkedIds.value)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    checkedIds.value = next
  }
  function clearChecked() {
    checkedIds.value = new Set()
  }

  // ── 快照抽屉 / 保存弹窗 / 回看选择器状态 ──
  const drawerVisible = ref(false)
  const saveDialogVisible = ref(false)
  const pickerVisible = ref(false)
  const saving = ref(false)

  // ── Actions ──

  async function fetchDevices() {
    try {
      const { data } = await apiGetDevices()
      if (data.status) devices.value = data.data?.devices || []
      else error.value = data.message || '设备列表加载失败'
    } catch (e) {
      error.value = '设备列表加载失败，请稍后重试'
    }
  }

  async function capture() {
    if (!captureSerial.value) {
      ElMessage.warning('请先选择设备')
      return
    }
    captLoading.value = true
    error.value = ''
    try {
      const { data } = await apiCapture(captureSerial.value, captureMethod.value)
      if (data.status) {
        applySnapshot(data.data)
        ElMessage.success(`获取成功（元素 ${data.data?.element_count ?? 0} · OCR ${data.data?.ocr_count ?? 0}）`)
        await fetchSnapshots()
        // 自动化结构化：获取成功后直接计算结构分区并切换到结构视图（PRD-03 结构分析）
        await analyzeSnapshot()
        return data.data
      }
      error.value = data.message || '获取失败'
      ElMessage.error(data.message || '获取失败')
    } catch (e) {
      ElMessage.error('获取失败')
    } finally {
      captLoading.value = false
    }
    return null
  }

  function applySnapshot(data) {
    ;(data.elements || []).forEach((e, i) => { e._idx = i })
    ;(data.texts || []).forEach((t, i) => { t._idx = i })
    snapshot.value = data
    selected.value = null
    selectedOcr.value = null
    filterMode.value = 'all'
    searchText.value = ''
    clearChecked()
    analysis.value = null
    viewMode.value = 'elements'
    nameOverrides.value = {}
  }

  async function fetchSnapshots() {
    try {
      const { data } = await apiGetSnapshots(0, 100)
      if (data.status) {
        snapshots.value = data.data?.items || []
        snapshotTotal.value = data.data?.total || 0
      } else {
        error.value = data.message || '快照列表加载失败'
      }
    } catch (e) {
      error.value = '快照列表加载失败，请稍后重试'
    }
  }

  async function viewSnapshot(id) {
    try {
      const { data } = await apiGetSnapshot(id)
      if (data.status) {
        applySnapshot(data.data)
        drawerVisible.value = false
        return data.data
      }
      ElMessage.error(data.message || '快照加载失败')
    } catch (e) {
      ElMessage.error('快照加载失败')
    }
    return null
  }

  async function analyzeSnapshot() {
    if (!snapshot.value?.snapshot_id) {
      ElMessage.warning('请先获取或选择快照')
      return
    }
    analyzing.value = true
    try {
      const { data } = await apiAnalyzeSnapshot(snapshot.value.snapshot_id)
      if (data.status) {
        analysis.value = data.data
        // 结构与快照元素同源同序（dump_json.elements），补 _idx 以联动左侧截图高亮
        ;(analysis.value.elements || []).forEach((e, i) => { e._idx = i })
        viewMode.value = 'structure'
        return data.data
      }
      ElMessage.error(data.message || '结构分析失败')
    } catch (e) {
      ElMessage.error('结构分析失败')
    } finally {
      analyzing.value = false
    }
    return null
  }

  async function deleteSnapshot(id) {
    try {
      const { data } = await apiDeleteSnapshot(id)
      if (data.status) {
        ElMessage.success('快照已删除')
        if (snapshot.value?.snapshot_id === id) {
          snapshot.value = null
          clearChecked()
        }
        await fetchSnapshots()
        return true
      }
      ElMessage.error(data.message || '删除失败')
    } catch (e) {
      ElMessage.error('删除失败')
    }
    return false
  }

  async function saveToElements(payload) {
    if (!snapshot.value) return null
    if (checkedIds.value.size === 0) {
      ElMessage.warning('请先勾选要保存的数据')
      return null
    }
    saving.value = true
    try {
      const body: {
        page_label: string; folder_path: string; include_ocr: boolean;
        element_ids?: number[]; page_id?: number; aliases?: Record<string, string>;
      } = {
        page_label: payload.pageLabel || '',
        folder_path: payload.folderPath || '',
        include_ocr: payload.includeOcr !== false,
      }
      if (payload.pageId) body.page_id = payload.pageId
      // 结构分析表内联重命名的「元素名称」→ 按 resource_id 映射为别名写入元素定位
      const all = snapshot.value.elements || []
      const aliases: Record<string, string> = {}
      for (const [idx, name] of Object.entries(nameOverrides.value)) {
        const rid = (all[Number(idx)]?.resource_id || '').trim()
        if (rid && name) aliases[rid] = name
      }
      if (Object.keys(aliases).length) body.aliases = aliases
      // 勾选 = 筛减：dump 行（含坐标匹配行）按元素索引筛减；勾了纯 OCR 行自动携带页面级 OCR
      const checkedDumpIdx = mergedRows.value
        .filter(r => r._kind === 'dump' && checkedIds.value.has(r._rowKey))
        .map(r => r._idx)
      const hasOcrChecked = mergedRows.value.some(r =>
        (r._kind === 'ocr' || r._ocrMatched) && checkedIds.value.has(r._rowKey)
      )
      if (checkedDumpIdx.length > 0 && checkedDumpIdx.length < all.length) {
        body.element_ids = checkedDumpIdx
      }
      if (payload.includeOcr !== false && hasOcrChecked) {
        body.include_ocr = true
      }
      const { data } = await apiSaveToElements(snapshot.value.snapshot_id, body)
      if (data.status) {
        const r = data.data || {}
        ElMessage.success(`已保存 ${r.saved ?? 0} 个元素（${r.updated ?? 0} 个已更新，${r.skipped ?? 0} 个跳过）`)
        saveDialogVisible.value = false
        await fetchSnapshots()
        return r
      }
      ElMessage.error(data.message || '保存失败')
    } catch (e) {
      ElMessage.error('保存失败')
    } finally {
      saving.value = false
    }
    return null
  }

  async function viewSavedPage(pageId) {
    try {
      const { data } = await apiGetPageView(pageId)
      if (data.status) {
        applySnapshot({
          snapshot_id: null,
          serial: '',
          method: 'saved',
          package: data.data?.package || '',
          activity: data.data?.activity || '',
          element_count: data.data?.element_count || 0,
          actionable_count: 0,
          elements: (data.data?.elements || []).map(e => ({
            class_name: e.class_name, text: e.text_val, content_desc: e.content_desc,
            resource_id: e.resource_id, bounds: e.bounds, xpaths: e.xpaths || [],
            x: e.x, y: e.y, width: e.width, height: e.height,
            clickable: e.clickable, enabled: e.enabled, scrollable: e.scrollable,
            checked: e.checked, thumbnail_path: e.thumbnail_path,
          })),
          ocr_count: data.data?.ocr_json?.ocr_count || 0,
          texts: (data.data?.ocr_json?.texts || []).map(t => ({
            text: t.text, confidence: t.confidence, x: t.x, y: t.y,
            width: t.width, height: t.height,
            bounds: t.bounds || `[${t.x},${t.y}][${(t.x || 0) + (t.width || 0)},${(t.y || 0) + (t.height || 0)}]`,
            thumbnail_path: t.thumbnail_path || '',
          })),
          screenshot_path: data.data?.screenshot_path || '',
          created_at: null,
        })
        pickerVisible.value = false
        return data.data
      }
      ElMessage.error(data.message || '页面加载失败')
    } catch (e) {
      ElMessage.error('页面加载失败')
    }
    return null
  }

  function selectElement(el) {
    selected.value = el
    selectedOcr.value = null
  }
  function selectOcr(item) {
    selectedOcr.value = item
    selected.value = null
  }
  /** 结构分析表内联重命名：空值视为撤销自定义名（回退元素 text） */
  function setElementName(idx, name) {
    if (idx == null) return
    const next = { ...nameOverrides.value }
    const v = (name || '').trim()
    if (v) next[idx] = v
    else delete next[idx]
    nameOverrides.value = next
  }
  function clearError() { error.value = '' }

  return {
    devices, captureSerial, captureMethod, availableDevices,
    snapshot, snapshots, snapshotTotal, captLoading, error,
    elements, ocrTexts, selected, selectedOcr, filterMode, searchText, filteredElements,
    nameOverrides, mergedRows, filteredRows, checkedIds,
    analysis, analyzing, viewMode,
    drawerVisible, saveDialogVisible, pickerVisible, saving,
    fetchDevices, capture, fetchSnapshots, viewSnapshot, deleteSnapshot, analyzeSnapshot,
    saveToElements, viewSavedPage,
    toggleCheck, clearChecked,
    selectElement, selectOcr, setElementName, clearError,
  }
})
