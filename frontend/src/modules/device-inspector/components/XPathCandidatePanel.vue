<script setup>
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { animate } from 'animejs'
import { formatApiError } from '@/shared/api-client'
import { useElementStore } from '../store'
import { apiGetPages, apiCreatePage, apiAddElementToPage } from '@/modules/element-locator/api'
import { bus } from '@/shared/event-bus'

const props = defineProps({ element: { type: Object, default: null } })
const emit = defineEmits(['add-step', 'do-action'])
const store = useElementStore()

// ── Idle animation ──
const emptyIconRef = ref(null)
const emptyTitleRef = ref(null)
let emptyAnimeInstances = []

function startEmptyAnimation() {
  stopEmptyAnimation()
  nextTick(() => {
    if (emptyIconRef.value) {
      emptyAnimeInstances.push(animate(emptyIconRef.value, {
        translateY: [-6, 6],
        duration: 2800,
        loop: true,
        ease: 'inOutSine',
        direction: 'alternate',
      }))
    }
    if (emptyTitleRef.value) {
      emptyAnimeInstances.push(animate(emptyTitleRef.value, {
        opacity: [0.5, 1],
        duration: 2800,
        loop: true,
        ease: 'inOutSine',
        direction: 'alternate',
      }))
    }
  })
}

function stopEmptyAnimation() {
  emptyAnimeInstances.forEach(inst => { try { inst.pause() } catch (_) {} })
  emptyAnimeInstances = []
}

watch(() => props.element, (el) => {
  if (el) {
    stopEmptyAnimation()
  } else {
    nextTick(() => startEmptyAnimation())
  }
}, { immediate: true })

onUnmounted(() => stopEmptyAnimation())

const inputVisible = ref(false)
const inputText = ref('')

// ── Save to element-manager ──
const saveVisible = ref(false)
const pagesLoading = ref(false)
const saving = ref(false)
const pages = ref([])
const saveCandidates = ref([])
const saveForm = ref({ pageId: null, alias: '', selectedXpath: '' })

function pageLabel(p) {
  return p.label || `Page #${p.id}`
}

async function openSaveDialog() {
  if (!props.element) return
  const rank = ['resource-id','text','content-desc','class','index','combined','resource-id (any)','text (any)']
  const prio = t => { const i = rank.indexOf(t); return i === -1 ? 999 : i }
  const candidates = (props.element.xpaths || [])
    .filter(x => x.count === 1 && x.xpath)
    .sort((a, b) => prio(a.type) - prio(b.type))
  if (!candidates.length) {
    ElMessage.warning('当前元素没有唯一定位策略（匹配数=1），无法保存')
    return
  }
  // Show dialog immediately, then load pages asynchronously
  const autoName = props.element.text || props.element.resource_id?.split('/').pop() || ''
  saveCandidates.value = candidates
  saveForm.value = {
    pageId: null,
    alias: autoName,
    selectedXpath: candidates[0].xpath,
  }
  saveVisible.value = true
  pagesLoading.value = true
  try {
    const { data } = await apiGetPages()
    if (data.status) pages.value = data.pages || []
  } catch (e) {
    ElMessage.error({ message: formatApiError(e, '加载页面列表失败'), duration: 4000, showClose: true })
  } finally {
    pagesLoading.value = false
  }
  saveForm.value.pageId = pages.value[0]?.id || null
  if (!saveForm.value.pageId) {
    const pkg = store.lastDump?.package || store.currentDevice?.package || ''
    const activity = store.lastDump?.activity || ''
    try {
      const { data } = await apiCreatePage({
        label: `Page_${new Date().toISOString().slice(0, 10)}`,
        package: pkg,
        activity,
      })
      if (data.status) {
        const page = data.page || {}
        saveForm.value.pageId = page.id
        pages.value.push({
          id: page.id,
          label: page.label || data.label,
        })
      } else {
        ElMessage.error(data.message || '自动创建页面失败')
      }
    } catch (e) {
      ElMessage.error({ message: formatApiError(e, '自动创建页面失败'), duration: 4000, showClose: true })
    }
  }
}

async function doSave() {
  if (!saveForm.value.pageId) { ElMessage.warning('请先选择目标页面'); return }
  if (!saveForm.value.alias.trim()) { ElMessage.warning('请输入元素名称'); return }
  const candidate = saveCandidates.value.find(c => c.xpath === saveForm.value.selectedXpath)
  if (!candidate) { ElMessage.warning('请选择唯一定位策略'); return }
  const el = props.element
  saving.value = true
  try {
    const { data } = await apiAddElementToPage(saveForm.value.pageId, {
      alias: saveForm.value.alias.trim(),
      xpath: candidate.xpath,
      xpath_candidates: saveCandidates.value,
      class_name: el.class_name || '',
      text_val: el.text || '',
      resource_id: el.resource_id || '',
      bounds: el.bounds || '',
      clickable: el.clickable || false,
      content_desc: el.content_desc || '',
    })
    if (data.status) {
      const name = saveForm.value.alias.trim()
      ElMessage.success({
        message: data.updated ? `元素「${name}」已更新` : `元素「${name}」已保存`,
        duration: 2500,
      })
      saveVisible.value = false
      // Notify element manager to refresh its table
      bus.emit('elements-saved', { pageId: saveForm.value.pageId })
    } else {
      ElMessage.warning({ message: data.message || '保存未完成，请检查填写内容', duration: 4000, showClose: true })
    }
  } catch (e) {
    const status = e.response?.status
    const hint = formatApiError(e, '保存元素失败，请稍后重试')
    if (status === 409 || hint.includes('已在当前页面')) {
      ElMessage.warning({ message: hint, duration: 5000, showClose: true })
    } else {
      ElMessage.error({ message: hint, duration: 5000, showClose: true })
    }
  } finally {
    saving.value = false
  }
}

function centerOf(el) {
  return {
    x: el.x + Math.round(el.width / 2),
    y: el.y + Math.round(el.height / 2),
  }
}

function doClick() {
  if (!props.element) return
  const c = centerOf(props.element)
  emit('do-action', 'click', c.x, c.y)
}

function doLongClick() {
  if (!props.element) return
  const c = centerOf(props.element)
  emit('do-action', 'longclick', c.x, c.y)
}

function openInput() {
  if (!props.element) return
  inputText.value = ''
  inputVisible.value = true
}

function doInput() {
  if (!props.element || !inputText.value.trim()) return
  const c = centerOf(props.element)
  emit('do-action', 'input', c.x, c.y, inputText.value.trim())
  inputVisible.value = false
}

async function copyXPath(xpath) {
  try {
    await navigator.clipboard.writeText(xpath)
  } catch (e) {
    // Fallback for non-HTTPS
    const ta = document.createElement('textarea')
    ta.value = xpath
    ta.style.position = 'fixed'; ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    console.error(e);
  }
}
</script>

<template>
  <div class="panel">
    <h3>XPath 候选</h3>

    <!-- Action bar (only when element selected) -->
    <div v-if="element" class="action-bar">
      <button class="xp-btn" @click="doClick">👆 点击</button>
      <button class="xp-btn" @click="openInput">⌨ 输入</button>
      <button class="xp-btn xp-btn--danger" @click="doLongClick">⏱ 长按</button>
      <button class="xp-btn xp-btn--primary" @click="openSaveDialog" style="margin-left:auto">💾 保存到元素管理</button>
    </div>

    <!-- Save to element-manager dialog -->
    <el-dialog
      v-model="saveVisible"
      title="保存到元素管理"
      width="420px"
      :close-on-click-modal="false"
      
      @close="saveVisible = false"
      
    >
      <div class="form-grid">
        <label class="form-label required">目标页面</label>
        <el-select
          v-model="saveForm.pageId"
          placeholder="选择页面"
          :disabled="pagesLoading"
          filterable
          style="width:100%"
        >
          <el-option
            v-for="p in pages"
            :key="p.id"
            :label="pageLabel(p)"
            :value="p.id"
          />
        </el-select>
        <label class="form-label required">元素名称</label>
        <el-input v-model="saveForm.alias" placeholder="如：登录按钮" size="medium" />
        <label class="form-label required">定位策略</label>
        <el-select
          v-model="saveForm.selectedXpath"
          placeholder="选择唯一定位策略"
          filterable
          style="width:100%"
        >
          <el-option
            v-for="c in saveCandidates"
            :key="c.xpath"
            :label="`${c.type} — ${c.xpath}`"
            :value="c.xpath"
          >
            <div class="xpath-opt">
              <span class="xpath-opt-type">{{ c.type }}</span>
              <span class="xpath-opt-path">{{ c.xpath }}</span>
            </div>
          </el-option>
        </el-select>
      </div>
      <template #footer>
        <button class="xp-btn" @click="saveVisible = false">取消</button>
        <button class="xp-btn xp-btn--primary" :disabled="saving || pagesLoading" @click="doSave">保存</button>
      </template>
    </el-dialog>

    <!-- Input dialog -->
    <el-dialog
      v-model="inputVisible"
      title="输入文本"
      width="340px"
      :close-on-click-modal="false"
      
      @close="inputVisible = false"
      
    >
      <el-input v-model="inputText" placeholder="输入要发送的文本" size="medium" />
      <template #footer>
        <button class="xp-btn" @click="inputVisible = false">取消</button>
        <button class="xp-btn xp-btn--primary" @click="doInput">发送</button>
      </template>
    </el-dialog>

    <!-- XPath table -->
    <div v-if="!element" class="empty">
        <span ref="emptyIconRef" class="empty-icon">🔍</span>
        <p ref="emptyTitleRef" class="empty-text">点击截图中元素查看 XPath</p>
      </div>
    <div v-else class="table-wrap">
      <!-- Element info section -->
      <div class="el-info">
        <div class="el-info__row">
          <span class="el-info__label">Class</span>
          <span class="el-info__value">{{ element.class_name || '—' }}</span>
        </div>
        <div class="el-info__row">
          <span class="el-info__label">Text</span>
          <span class="el-info__value">{{ element.text || '—' }}</span>
        </div>
        <div class="el-info__row">
          <span class="el-info__label">ID</span>
          <span class="el-info__value">{{ element.resource_id || '—' }}</span>
        </div>
        <div class="el-info__row">
          <span class="el-info__label">Bounds</span>
          <span class="el-info__value">{{ element.bounds || '—' }}</span>
        </div>
        <div class="el-info__row">
          <span class="el-info__label">Clickable</span>
          <span class="el-info__value" :class="{ 'clickable-yes': element.clickable }">
            {{ element.clickable ? '✓ 是' : '✗ 否' }}
          </span>
        </div>
      </div>
      <el-divider style="margin: 8px 0" />
      <el-table
        :data="element.xpaths || []"
        size="small"
        style="width: 100%"
      >
        <el-table-column prop="type" label="策略" width="120" />
        <el-table-column prop="xpath" label="XPath" show-overflow-tooltip min-width="200" />
        <el-table-column prop="count" label="匹配数" width="60" align="center" />
        <el-table-column label="" width="50" align="center">
          <template #default="{ row }">
            <button class="xp-btn-icon" title="复制" @click="copyXPath(row.xpath)">📋</button>
          </template>
        </el-table-column>
        <el-table-column label="" width="50" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="emit('add-step', row)">+</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.panel {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--app-bg-card));
  
  border-radius: 20px;
  border: 1px solid var(--ink));
  padding: 16px;
  box-shadow: var(--app-shadow-sm, 0 4px 15px rgba(0,0,0,0.02));
  overflow: hidden;
}
.panel::before {
  content: '';
  position: absolute;
  top: 4px; left: 50%; transform: translateX(-50%);
  width: 9px; height: 9px;
  background: radial-gradient(circle, var(--app-pushpin-light) 30%, var(--app-pushpin-mid) 60%, var(--app-pushpin-dark) 100%);
  border-radius: 50%;
  box-shadow: 0 1px 1px rgba(0,0,0,0.08);
  z-index: 2;
}
h3 {
  font-size: var(--app-size-sm);
  color: var(--app-text, var(--app-ink));
  margin-bottom: 12px;
  flex-shrink: 0;
}
.action-bar { border-radius: 6px 10px 6px 10px;
  display: flex; gap: 6px; margin-bottom: 10px; flex-shrink: 0;
  padding: 8px; background: rgba(255,255,255,0.03);
  border-radius: 8px; border: 1px solid var(--ink));
}
.empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--app-text-secondary, var(--app-ink-muted));
  font-size: var(--app-size-sm);
}
.empty-icon {
  font-size: var(--app-size-2xl);
  opacity: 0.55;
}
.empty-text {
  margin: 0;
  font-size: var(--app-size-sm);
  font-weight: 500;
  color: var(--app-text, var(--ink));
}
.table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
}
.el-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 4px;
  padding: 8px 10px;
  background: rgba(179, 158, 243,0.04);
  border-radius: 8px;
}
.el-info__row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: var(--app-size-sm);
}
.el-info__label {
  min-width: 56px;
  font-weight: 600;
  color: var(--app-text, var(--app-ink));
  flex-shrink: 0;
}
.el-info__value {
  color: var(--app-text-secondary, var(--app-ink-muted));
  word-break: break-all;
  line-height: 1.4;
}
.clickable-yes {
  color: var(--c-workflow);
  font-weight: 600;
}
.form-grid {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 14px 10px;
  align-items: center;
}
.form-label {
  text-align: right;
  font-size: var(--app-size-sm);
  color: var(--text-secondary, var(--app-ink-muted));
  font-weight: 500;
  user-select: none;
}
.form-label.required::before {
  content: '*';
  color: var(--el-color-danger, #FFB5A7);
  margin-right: 3px;
}
.xpath-opt {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.3;
  padding: 2px 0;
}
.xpath-opt-type {
  font-size: var(--app-size-sm);
  font-weight: 600;
  color: var(--text-primary, var(--app-ink));
}
.xpath-opt-path {
  font-size: var(--app-size-xs);
  color: var(--text-secondary, var(--app-ink-muted));
  word-break: break-all;
}

/* Paper buttons */
.xp-btn {
  font-size: var(--app-size-xs); font-weight: 700; padding: 4px 12px;
  border: 2px solid var(--app-ink, #2d2d2d); border-radius: 4px 8px 4px 8px;
  background: var(--app-bg-card); color: var(--app-ink, #2d2d2d);
  cursor: pointer; font-family: inherit; transition: all 0.12s; white-space: nowrap;
}
.xp-btn:hover { background: var(--app-highlight, #FFE066); }
.xp-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.xp-btn--primary { background: var(--app-ink, #2d2d2d); color: var(--app-bg-card); }
.xp-btn--primary:hover { opacity: 0.85; color: var(--app-bg-card); }
.xp-btn--danger { color: var(--app-disconnect-text); border-color: var(--app-disconnect-text); }
.xp-btn--danger:hover { background: var(--app-status-danger-bg, #FFE0DB); }
.xp-btn-icon {
  font-size: var(--app-size-sm); padding: 2px 6px; border: 1.5px solid var(--app-ink, #2d2d2d);
  border-radius: 3px 6px 3px 6px; background: var(--app-bg-card); cursor: pointer;
  transition: all 0.12s; color: var(--app-ink, #2d2d2d);
}
.xp-btn-icon:hover { background: var(--app-highlight, #FFE066); }
</style>
