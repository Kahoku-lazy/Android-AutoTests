<script setup lang="ts">
/**
 * 从「测试用例」模块多选导入 → 工作流 test_case 文档
 */
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { listDefinitions } from '@/modules/case-manager/api.js'
import { fromCaseManagerSteps } from '@/modules/workflow/composables/caseBridge'
import { useLibraryStore } from '@/modules/workflow/stores/libraryStore'

export type PlatformCaseRow = {
  id: string
  title: string
  package_name?: string
  enabled?: boolean
  steps_data?: unknown[]
  description?: string
  priority?: string
}

const props = defineProps<{
  modelValue: boolean
  /** 导入目标目录（library folder id，含 folder: 前缀或 null=根） */
  targetFolderId: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  imported: [nodeIds: string[]]
}>()

const lib = useLibraryStore()
const loading = ref(false)
const importing = ref(false)
const keyword = ref('')
const rows = ref<PlatformCaseRow[]>([])
const selected = ref<Set<string>>(new Set())

const open = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
})

/** 已关联过的平台用例 id → 工作流文档数 */
const linkedCount = computed(() => {
  const map = new Map<string, number>()
  for (const n of lib.nodes) {
    if (n.type !== 'test_case') continue
    const cfg = lib.configCache[n.id] as { linkedCaseId?: string } | undefined
    const lid = cfg?.linkedCaseId
    if (lid) map.set(lid, (map.get(lid) || 0) + 1)
  }
  return map
})

const filtered = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return rows.value
  return rows.value.filter(
    (r) =>
      r.title?.toLowerCase().includes(q) ||
      r.id?.toLowerCase().includes(q) ||
      (r.package_name || '').toLowerCase().includes(q)
  )
})

const selectedCount = computed(() => selected.value.size)

async function loadList() {
  loading.value = true
  selected.value = new Set()
  try {
    const { data } = await listDefinitions()
    if (!data?.ok) throw new Error(data?.error || '加载用例失败')
    rows.value = (data.definitions || []) as PlatformCaseRow[]
  } catch (e: any) {
    rows.value = []
    ElMessage.error(e?.message || '加载用例库失败')
  } finally {
    loading.value = false
  }
}

watch(
  () => props.modelValue,
  (v) => {
    if (v) {
      keyword.value = ''
      loadList()
    }
  }
)

function toggle(id: string) {
  const next = new Set(selected.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selected.value = next
}

function toggleAllVisible() {
  const ids = filtered.value.map((r) => r.id)
  const allOn = ids.length > 0 && ids.every((id) => selected.value.has(id))
  const next = new Set(selected.value)
  if (allOn) ids.forEach((id) => next.delete(id))
  else ids.forEach((id) => next.add(id))
  selected.value = next
}

function close() {
  open.value = false
}

async function confirmImport() {
  if (!selected.value.size) {
    ElMessage.warning('请至少选择一条用例')
    return
  }
  importing.value = true
  const createdIds: string[] = []
  let ok = 0
  let fail = 0
  try {
    const list = rows.value.filter((r) => selected.value.has(r.id))
    for (const c of list) {
      try {
        const blocks = fromCaseManagerSteps(c.steps_data || [])
        const node = await lib.createTestCase(c.title || c.id, props.targetFolderId, {
          packageName: c.package_name || 'com.example.app',
          syncPlatform: false,
          blocks,
          linkedCaseId: c.id,
        })
        createdIds.push(node.id)
        ok += 1
      } catch {
        fail += 1
      }
    }
    if (ok) {
      ElMessage.success(
        fail ? `已导入 ${ok} 条，失败 ${fail} 条` : `已导入 ${ok} 条用例`
      )
      emit('imported', createdIds)
      close()
    } else {
      ElMessage.error('导入失败，请重试')
    }
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <el-dialog
    v-model="open"
    title="从用例库导入"
    width="640px"
    :close-on-click-modal="false"
    append-to-body
    class="wf-import-cases-dialog"
  >
    <p class="hint">
      将「测试用例」模块中的用例转为工作流积木文档，写入当前选中目录。
      步骤会平铺转换；已关联的用例会标注「已导入」。
    </p>
    <div class="toolbar">
      <el-input
        v-model="keyword"
        clearable
        placeholder="搜索标题 / ID / 包名"
        class="search"
      />
      <el-button size="small" @click="toggleAllVisible">
        {{
          filtered.length && filtered.every((r) => selected.has(r.id))
            ? '取消全选'
            : '全选当前'
        }}
      </el-button>
      <span class="count">已选 {{ selectedCount }} / 共 {{ rows.length }}</span>
    </div>

    <div v-loading="loading" class="list">
      <div v-if="!loading && !filtered.length" class="empty">暂无用例，请先在「测试用例」中创建</div>
      <label
        v-for="row in filtered"
        :key="row.id"
        class="row"
        :class="{ on: selected.has(row.id) }"
      >
        <input
          type="checkbox"
          :checked="selected.has(row.id)"
          @change="toggle(row.id)"
        />
        <div class="meta">
          <div class="title-line">
            <span class="title">{{ row.title || row.id }}</span>
            <span v-if="linkedCount.get(row.id)" class="tag linked">已导入 ×{{ linkedCount.get(row.id) }}</span>
            <span v-if="row.enabled === false" class="tag off">已禁用</span>
          </div>
          <div class="sub">
            <span>{{ row.id }}</span>
            <span v-if="row.package_name">· {{ row.package_name }}</span>
            <span>· {{ (row.steps_data || []).length }} 步</span>
          </div>
        </div>
      </label>
    </div>

    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button
        type="primary"
        :loading="importing"
        :disabled="!selectedCount"
        @click="confirmImport"
      >
        导入 {{ selectedCount ? `(${selectedCount})` : '' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.hint {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 600;
  color: #999;
  line-height: 1.45;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.search { flex: 1; }
.count {
  font-size: 12px;
  font-weight: 700;
  color: var(--ink);
  white-space: nowrap;
}
.list {
  max-height: 360px;
  overflow: auto;
  border: 1px solid var(--ink);
  border-radius: 12px;
  background: rgba(255,255,255,0.48);
}
.empty {
  padding: 32px 16px;
  text-align: center;
  font-size: 13px;
  font-weight: 700;
  color: #999;
}
.row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(162,210,255,0.16);
  cursor: pointer;
  margin: 0;
}
.row:last-child { border-bottom: none; }
.row:hover { background: rgba(162,210,255,0.12); }
.row.on { background: rgba(162,210,255,0.18); }
.row input { margin-top: 3px; accent-color: var(--app-green-deep); }
.meta { min-width: 0; flex: 1; }
.title-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.title {
  font-size: 13px;
  font-weight: 800;
  color: var(--ink);
}
.sub {
  margin-top: 2px;
  font-size: 11px;
  font-weight: 600;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tag {
  font-size: 10px;
  font-weight: 800;
  padding: 1px 7px;
  border-radius: 999px;
}
.tag.linked {
  background: rgba(162,210,255,0.18);
  color: var(--app-green-deep);
}
.tag.off {
  background: rgba(232, 95, 95, 0.12);
  color: #e85f5f;
}
</style>
