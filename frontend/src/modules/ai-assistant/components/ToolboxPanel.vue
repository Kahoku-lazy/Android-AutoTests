<template>
  <div class="toolbox-host">
    <div class="toolbox-header">
      <h3 class="toolbox-title">🧰 AI 工具箱</h3>
      <span class="toolbox-subtitle">共享 Skill、MCP 工具与扩展 — 多智能体可复用</span>
      <div class="toolbox-actions">
        <button class="tb-btn tb-btn-primary" @click="openMcpDialog()">+ MCP 工具</button>
        <label class="tb-btn tb-btn-outline">
          + Skill 文件夹
          <input
            type="file"
            webkitdirectory
            multiple
            hidden
            @change="onSkillFolderPicked"
          />
        </label>
      </div>
    </div>

    <div class="toolbox-filters">
      <button
        v-for="f in filters"
        :key="f.key"
        class="tb-filter-btn"
        :class="{ active: activeFilter === f.key }"
        @click="activeFilter = f.key"
      >
        {{ f.label }}
      </button>
    </div>

    <div v-loading="loading" class="toolbox-grid">
      <EmptyState v-if="!loading && filteredItems.length === 0" icon="🧰" text="暂无共享工具，点击上方按钮添加" />
      <div
        v-for="item in filteredItems"
        :key="item.id"
        class="tb-card"
      >
        <div class="tb-card-header">
          <span class="tb-card-name">{{ item.name }}</span>
          <span class="tb-card-type" :class="'tb-type-' + item.item_type">
            {{ typeLabel(item.item_type) }}
          </span>
        </div>
        <div class="tb-card-body">
          <p v-if="item.description" class="tb-card-desc">{{ item.description }}</p>
          <pre v-if="item.config_json && item.config_json !== '{}'" class="tb-card-config">{{
            formatConfig(item.config_json)
          }}</pre>
        </div>
        <div class="tb-card-footer">
          <span class="tb-card-date">{{ item.created_at?.slice(0, 10) }}</span>
          <button class="tb-card-btn" @click="editItem(item)">编辑</button>
          <button class="tb-card-btn danger" @click="removeItem(item)">删除</button>
        </div>
      </div>
    </div>

    <!-- MCP / Extension edit dialog (reuses AgentMcpDialog pattern) -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑' : '添加 MCP 工具 / 扩展'"
      width="520px"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="例如: GitHub MCP Server" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.item_type" style="width:100%">
            <el-option label="MCP 工具" value="mcp" />
            <el-option label="扩展" value="extension" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="此工具的用途说明" />
        </el-form-item>
        <el-form-item label="配置 JSON">
          <el-input
            v-model="form.config_json"
            type="textarea"
            :rows="6"
            placeholder='{"transport":"stdio","command":"npx","args":["-y","..."]}'
            class="tb-json-input"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveItem">
          {{ editingId ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import {
  fetchSharedTools,
  createSharedTool,
  updateSharedTool,
  deleteSharedTool,
  uploadSharedSkill,
} from '../api.js'

const items = ref([])
const loading = ref(false)
const activeFilter = ref('all')
const filters = [
  { key: 'all', label: '全部' },
  { key: 'mcp', label: 'MCP 工具' },
  { key: 'skill', label: 'Skill' },
  { key: 'extension', label: '扩展' },
]

const filteredItems = computed(() => {
  if (activeFilter.value === 'all') return items.value
  return items.value.filter((i) => i.item_type === activeFilter.value)
})

function typeLabel(t) {
  return { mcp: 'MCP', skill: 'Skill', extension: '扩展' }[t] || t
}

function formatConfig(raw) {
  try { return JSON.stringify(JSON.parse(raw), null, 2) } catch { return raw }
}

async function loadItems() {
  loading.value = true
  try {
    const data = await fetchSharedTools()
    if (data.ok) items.value = data.items || []
  } catch (e) { console.error('Failed to load toolbox:', e) }
  loading.value = false
}

// ── MCP / Extension dialog ──
const dialogVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = ref({ name: '', item_type: 'mcp', description: '', config_json: '{}' })

function openMcpDialog() {
  editingId.value = null
  form.value = { name: '', item_type: 'mcp', description: '', config_json: '{}' }
  dialogVisible.value = true
}

function editItem(item) {
  editingId.value = item.id
  form.value = {
    name: item.name,
    item_type: item.item_type,
    description: item.description,
    config_json: formatConfig(item.config_json),
  }
  dialogVisible.value = true
}

async function saveItem() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入名称'); return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updateSharedTool(editingId.value, { ...form.value })
      ElMessage.success('已更新')
    } else {
      await createSharedTool({ ...form.value })
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await loadItems()
  } catch (e) { ElMessage.error('操作失败') }
  saving.value = false
}

async function removeItem(item) {
  try {
    await ElMessageBox.confirm(`确定要删除 "${item.name}" 吗？`, '确认删除', { type: 'warning' })
  } catch { return }
  try {
    const data = await deleteSharedTool(item.id)
    if (data.ok) {
      ElMessage.success('已删除')
      items.value = items.value.filter((i) => i.id !== item.id)
    }
  } catch (e) { ElMessage.error('删除失败') }
}

// ── Skill folder upload ──
async function onSkillFolderPicked(e) {
  const files = Array.from(e.target.files || [])
  if (!files.length) return
  const folderName = files[0].webkitRelativePath?.split('/')[0] || 'skill'
  const fd = new FormData()
  fd.append('name', folderName)
  files.forEach((f) => fd.append('files', f))
  loading.value = true
  try {
    const data = await uploadSharedSkill(fd)
    if (data.ok) {
      ElMessage.success('Skill 文件夹已上传')
      await loadItems()
    } else {
      ElMessage.error(data.error || '上传失败')
    }
  } catch (e) { ElMessage.error('上传失败') }
  loading.value = false
  e.target.value = ''
}

onMounted(() => loadItems())
</script>

<style scoped>
.toolbox-host {
  padding: 16px 20px 32px;
  height: 100%;
  overflow-y: auto;
}
.toolbox-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}
.toolbox-title { font-size: 18px; font-weight: 700; color: var(--app-text-primary, #2c2c2c); margin: 0; }
.toolbox-subtitle { font-size: 13px; color: var(--app-text-secondary, #888); flex: 1; }
.toolbox-actions { display: flex; gap: 8px; }
.tb-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600;
  border: none; cursor: pointer; font-family: inherit; transition: all 0.15s;
}
.tb-btn-primary { background: #6c5ce7; color: #fff; }
.tb-btn-primary:hover { background: #5a4bd1; }
.tb-btn-outline { background: #fff; color: #6c5ce7; border: 1.5px solid #6c5ce7; }
.tb-btn-outline:hover { background: #f5f3ff; }
.toolbox-filters { display: flex; gap: 6px; margin-bottom: 16px; }
.tb-filter-btn {
  padding: 6px 14px; border-radius: 8px; border: 1px solid var(--app-border, #e0e0e0);
  background: #fff; font-size: 13px; font-weight: 600; cursor: pointer;
  font-family: inherit; color: var(--app-text-secondary, #666); transition: all 0.15s;
}
.tb-filter-btn.active { background: #6c5ce7; color: #fff; border-color: #6c5ce7; }
.toolbox-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }
.tb-card {
  background: #fff; border-radius: 12px; border: 1px solid var(--app-border, #e8e8e8);
  padding: 14px 16px; display: flex; flex-direction: column; gap: 8px;
  transition: box-shadow 0.15s;
}
.tb-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.06); }
.tb-card-header { display: flex; align-items: center; gap: 8px; }
.tb-card-name { font-weight: 700; font-size: 15px; color: var(--app-text-primary, #2c2c2c); flex:1; }
.tb-card-type { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; }
.tb-type-mcp { background: #e8f5e9; color: #2e7d32; }
.tb-type-skill { background: #e3f2fd; color: #1565c0; }
.tb-type-extension { background: #fff3e0; color: #e65100; }
.tb-card-body { flex: 1; }
.tb-card-desc { font-size: 13px; color: var(--app-text-secondary, #666); margin: 0; }
.tb-card-config { font-size: 11px; color: #888; background: #f8f8f8; padding: 6px 8px;
  border-radius: 6px; margin: 4px 0 0; overflow-x: auto; white-space: pre-wrap; }
.tb-card-footer { display: flex; align-items: center; gap: 8px; }
.tb-card-date { font-size: 11px; color: #aaa; flex: 1; }
.tb-card-btn {
  font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 6px;
  border: 1px solid var(--app-border, #ddd); background: #fff; cursor: pointer;
  font-family: inherit; color: var(--app-text-secondary, #555);
}
.tb-card-btn:hover { background: #f5f5f5; }
.tb-card-btn.danger { color: #c43f3f; border-color: #f5d5d5; }
.tb-card-btn.danger:hover { background: #fef0f0; }
.tb-json-input :deep(textarea) { font-family: monospace; font-size: 12px; }
</style>
