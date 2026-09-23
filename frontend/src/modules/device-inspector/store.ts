/** device-inspector Pinia store — 快照中心：设备列表 / capture / 五分组分层视图 / 快照回看删除 */
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import { formatApiError } from '@/shared/api-client'
import {
  KEY_DISABLED_MESSAGE,
  LAYER_GROUPS,
  NO_SELECTION_MESSAGE,
  elementInGroup,
  groupCount,
} from './constants'
import {
  apiCapture,
  apiGetSnapshots,
  apiGetLayers,
  apiDeleteSnapshot,
  apiClearSnapshots,
  apiSaveToElements,
  apiGetDevices,
} from './api'

// 执行引擎占用前缀：不可用于 capture
const EXEC_PREFIXES = ['runner-', 'ai_agent', 'task-', 'run-']

function isExecutionOccupied(device) {
  return device.status === 'BUSY' && device.occupied_by &&
    EXEC_PREFIXES.some(p => device.occupied_by.startsWith(p))
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

  const availableDevices = computed(() =>
    devices.value.filter(d =>
      (d.status === 'ONLINE' || d.status === 'BUSY') && !isExecutionOccupied(d)
    )
  )

  // ── Snapshot / layers state ──
  /** 分层响应全量：{snapshot_id, source, package, activity, screen, screenshot_path, summary, total_matched, elements} */
  const layers = ref(null)
  /** 视图元信息（模板只消费这几个字段，与响应形状解耦） */
  const snapshot = ref(null)
  const snapshots = ref([])       // 快照列表 items
  const snapshotTotal = ref(0)
  const captLoading = ref(false)
  /** 失败记录：message 为经共享净化的可读原因；source 供「重试」重发对应请求 */
  const error = ref(null)
  const lastFailedSnapshotId = ref(null)

  // ── 分组（五个，固定顺序；切分组只改本地展示范围，不发请求）──
  const activeGroupId = ref(LAYER_GROUPS[0].id)
  const activeGroup = computed(
    () => LAYER_GROUPS.find(g => g.id === activeGroupId.value) || LAYER_GROUPS[0]
  )
  /** 分组徽标（计数来自后端摘要，切分组时保持不变） */
  const groupBadges = computed(() =>
    LAYER_GROUPS.map(g => ({ ...g, count: groupCount(layers.value?.summary, g) }))
  )

  /** 全量元素（坐标顺序由后端给定，含被展示裁剪丢弃的） */
  const elements = computed(() => layers.value?.elements || [])
  /** 当前分组的元素（同一批对象引用，截图联动与表格共用） */
  const groupElements = computed(() =>
    elements.value.filter(el => elementInGroup(el, activeGroup.value))
  )
  /** 数据来源：index=全量节点索引；legacy=历史快照降级为保留集 */
  const layerSource = computed(() => layers.value?.source || '')

  const selected = ref(null)      // 选中元素（截图联动）
  const nameOverrides = ref<Record<string, string>>({})   // { [元素 seq]: 自定义元素名称 }（表格内联重命名）

  // ── 勾选（保存到元素定位的筛减；key = _rowKey，即 `s{seq}`）──
  const checkedIds = ref(new Set())

  /**
   * 勾选集合 → 元素序号（1 基，与元素表「序号」列同源）。
   * 后端按该序号在快照全量节点索引中取元素，不再使用展示保留集的下标。
   */
  function checkedSeqs() {
    const seqs = []
    for (const key of checkedIds.value) {
      const seq = Number(String(key).replace(/^s/, ''))
      if (Number.isInteger(seq) && seq > 0) seqs.push(seq)
    }
    return seqs.sort((a, b) => a - b)
  }
  /** 勾选数量（入口守卫与提示共用，避免先把非法行键算进去） */
  const checkedCount = computed(() => checkedSeqs().length)

  function toggleCheck(row) {
    if (!row || typeof row !== 'object') return
    const id = row._rowKey ?? row._idx
    if (id == null) return
    const next = new Set(checkedIds.value)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    checkedIds.value = next
  }
  function clearChecked() {
    checkedIds.value = new Set()
  }

  // ── 快照抽屉 / 保存弹窗状态 ──
  const drawerVisible = ref(false)
  const saveDialogVisible = ref(false)
  const saving = ref(false)

  // ── Actions ──

  /** 统一失败出口：字符串直接作为原因（异常 2xx 的后端 message），错误对象经共享净化取原因 */
  function setError(source, reason, fallback) {
    const message = typeof reason === 'string' ? (reason || fallback) : formatApiError(reason, fallback)
    error.value = { message, source }
    return message
  }

  /** 同一来源的请求成功即撤掉该来源的失败提示，避免旧错误常驻 */
  function clearErrorFor(source) {
    if (error.value?.source === source) error.value = null
  }

  /** 「重试」按失败来源重发对应请求，而不是只清提示 */
  async function retry() {
    const source = error.value?.source
    if (!source) return
    if (source === 'devices') return fetchDevices()
    if (source === 'snapshots') return fetchSnapshots()
    if (source === 'capture') return capture()
    const id = lastFailedSnapshotId.value
    if (id == null) return
    if (source === 'layers') return fetchLayers(id)
    if (snapshot.value?.snapshot_id === id) return fetchLayers(id)
    return null
  }

  async function fetchDevices() {
    try {
      const { data } = await apiGetDevices()
      if (data.status) {
        devices.value = data.data?.devices || []
        clearErrorFor('devices')
      } else {
        setError('devices', data.message, '设备列表加载失败')
      }
    } catch (e) {
      setError('devices', e, '设备列表加载失败')
    }
  }

  async function capture() {
    if (!captureSerial.value) {
      notifyKeyUnavailable()
      return
    }
    captLoading.value = true
    error.value = null
    try {
      // 抓取方式恒为 dump（OCR 链路已下线，后端 method 入参保留但前端不再发 ocr）
      const { data } = await apiCapture(captureSerial.value, 'dump')
      if (data.status) {
        ElMessage.success(`获取成功（元素 ${data.data?.element_count ?? 0}）`)
        await fetchSnapshots()
        // 分层数据与快照同源：拿到 id 后立即拉分层（含被展示裁剪丢弃的元素）
        await fetchLayers(data.data?.snapshot_id)
        return data.data
      }
      ElMessage.error(setError('capture', data.message, '获取失败'))
    } catch (e) {
      ElMessage.error(setError('capture', e, '获取失败'))
    } finally {
      captLoading.value = false
    }
    return null
  }

  /** 分层响应 → 视图状态：元素逐个补行键与联动下标，并默认选中第一个非空分组 */
  function applyLayers(data) {
    const list = data?.elements || []
    list.forEach(el => {
      el._idx = el.seq
      el._rowKey = `s${el.seq}`
    })
    layers.value = { ...data, elements: list }
    snapshot.value = {
      snapshot_id: data?.snapshot_id ?? null,
      serial: '',
      package: data?.package || '',
      activity: data?.activity || '',
      screen_w: data?.screen?.w || 0,
      screen_h: data?.screen?.h || 0,
      screenshot_path: data?.screenshot_path || '',
      element_count: data?.summary?.total || list.length,
    }
    selected.value = null
    clearChecked()
    nameOverrides.value = {}
    const firstNonEmpty = groupBadges.value.find(g => g.count > 0)
    activeGroupId.value = (firstNonEmpty || groupBadges.value[0]).id
  }

  async function fetchLayers(id) {
    if (!id) return null
    lastFailedSnapshotId.value = id
    try {
      const { data } = await apiGetLayers(id)
      if (data.status) {
        applyLayers(data.data)
        clearErrorFor('layers')
        return data.data
      }
      ElMessage.error(setError('layers', data.message, '元素数据加载失败'))
    } catch (e) {
      ElMessage.error(setError('layers', e, '元素数据加载失败'))
    }
    return null
  }

  async function fetchSnapshots() {
    try {
      const { data } = await apiGetSnapshots(0, 100)
      if (data.status) {
        snapshots.value = data.data?.items || []
        snapshotTotal.value = data.data?.total || 0
        clearErrorFor('snapshots')
      } else {
        setError('snapshots', data.message, '快照列表加载失败')
      }
    } catch (e) {
      setError('snapshots', e, '快照列表加载失败')
    }
  }

  async function viewSnapshot(id) {
    const data = await fetchLayers(id)
    if (data) drawerVisible.value = false
    return data
  }

  async function deleteSnapshot(id) {
    try {
      const { data } = await apiDeleteSnapshot(id)
      if (data.status) {
        ElMessage.success('快照已删除')
        if (snapshot.value?.snapshot_id === id) {
          // 回到与 applyLayers 一致的空态：分层数据、元信息与选中元素一起清，
          // 否则表格会继续渲染已删快照的元素
          layers.value = null
          snapshot.value = null
          selected.value = null
          clearChecked()
        }
        await fetchSnapshots()
        return true
      }
      ElMessage.error(data.message || '删除失败')
    } catch (e) {
      ElMessage.error(formatApiError(e, '删除失败'))
    }
    return false
  }

  /** 一键清空：删除本人全部历史快照；成功后列表与分层状态一起复位（正在展示的那份也已被删） */
  async function clearSnapshots() {
    try {
      const { data } = await apiClearSnapshots()
      if (data.status) {
        const deleted = data.data?.deleted ?? 0
        ElMessage.success(`已清空 ${deleted} 条历史快照`)
        // 全部记录已删除，直接回到与 applyLayers 一致的无快照空态，无需再逐条判断
        layers.value = null
        snapshot.value = null
        selected.value = null
        clearChecked()
        nameOverrides.value = {}
        await fetchSnapshots()
        return deleted
      }
      ElMessage.error(data.message || '清空失败')
    } catch (e) {
      ElMessage.error(formatApiError(e, '清空失败'))
    }
    return null
  }

  async function saveToElements(payload) {
    if (!snapshot.value) return null
    const seqs = checkedSeqs()
    if (seqs.length === 0) {
      ElMessage.warning(NO_SELECTION_MESSAGE)
      return null
    }
    saving.value = true
    try {
      const body: {
        page_label: string; folder_path: string;
        element_ids: number[]; page_id?: number;
        element_aliases?: { index: number; name: string }[];
      } = {
        page_label: payload.pageLabel || '',
        folder_path: payload.folderPath || '',
        element_ids: seqs,
      }
      if (payload.pageId) body.page_id = payload.pageId
      // 表格内联重命名的「元素名称」→ 按元素序号逐元素回填；
      // 不能再按 resource_id 组装（同名 rid 的多个元素会被同一个名字覆盖）
      const elementAliases: { index: number; name: string }[] = []
      for (const [seq, name] of Object.entries(nameOverrides.value)) {
        const i = Number(seq)
        const v = (name || '').trim()
        if (Number.isInteger(i) && i > 0 && v) elementAliases.push({ index: i, name: v })
      }
      if (elementAliases.length) body.element_aliases = elementAliases
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
      ElMessage.error(formatApiError(e, '保存失败'))
    } finally {
      saving.value = false
    }
    return null
  }


  function selectElement(el) {
    selected.value = el
  }
  /** 表格内联重命名：空值视为撤销自定义名（回退元素 text） */
  function setElementName(idx, name) {
    if (idx == null) return
    const next = { ...nameOverrides.value }
    const v = (name || '').trim()
    if (v) next[idx] = v
    else delete next[idx]
    nameOverrides.value = next
  }
  /** 统一提示出口：冻结入口与不可用按键都走它，避免提示在两处各写一遍 */
  function notify(message) {
    if (message) ElMessage.warning(message)
  }
  /** 点击不可用（灰底）按键：不发请求，只说明不可用原因 */
  function notifyKeyUnavailable() {
    notify(KEY_DISABLED_MESSAGE)
  }

  return {
    captureSerial, availableDevices,
    layers, snapshot, layerSource, groupBadges, activeGroup, activeGroupId, groupElements, elements,
    snapshots, snapshotTotal, captLoading, error,
    selected, nameOverrides, checkedIds, checkedCount,
    drawerVisible, saveDialogVisible, saving,
    fetchDevices, capture, fetchSnapshots, fetchLayers, viewSnapshot, deleteSnapshot,
    clearSnapshots, saveToElements,
    toggleCheck,
    selectElement, setElementName, retry, notify, notifyKeyUnavailable,
  }
})
