<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { animate, stagger } from 'animejs'
import { ElMessage, ElMessageBox, ElTag } from 'element-plus'
import client from '@/shared/api-client.js'
import { Button as AnimalButton, Card, Table, Tabs } from 'animal-island-vue'
import PageHeader from '@/shared/components/PageHeader.vue'

const router = useRouter()
const definitions = ref([])
const loading = ref(false)
const activeFilter = ref('all')

onMounted(() => loadDefs())

async function loadDefs() {
  loading.value = true
  try { const { data } = await client.get('/cases/definitions'); if (data.ok) definitions.value = data.definitions } catch (_) {}
  loading.value = false
  await nextTick()
  animate('.case-table tbody tr', { opacity: [0,1], translateY: [16,0], delay: stagger(40), duration: 380, ease: 'outCubic' })
}

// ── Category tabs ──
const filterTabs = computed(() => {
  const cats = [...new Set(definitions.value.map(d => d.category).filter(Boolean))]
  return [
    { key: 'all', label: '全部' },
    { key: 'enabled', label: '已启用' },
    ...cats.map(c => ({ key: c, label: c })),
  ]
})
const filteredDefs = computed(() => {
  if (activeFilter.value === 'all') return definitions.value
  if (activeFilter.value === 'enabled') return definitions.value.filter(d => d.enabled)
  return definitions.value.filter(d => d.category === activeFilter.value)
})

// ── Table columns ──
const columns = [
  { title: 'ID', dataIndex: 'id', width: '200px' },
  { title: '标题', dataIndex: 'title' },
  { title: '分类', dataIndex: 'category', width: '120px' },
  { title: '启用', dataIndex: 'enabled', width: '80px', align: 'center' },
  { title: '操作', dataIndex: 'actions', width: '160px', align: 'center' },
]

function create() { router.push('/cases/new') }
function edit(row) { router.push(`/cases/${row.id}/edit`) }
async function remove(row) {
  try {
    await ElMessageBox.confirm(`删除用例「${row.title}」？`, '确认删除', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' })
    await client.delete(`/cases/definitions/${row.id}`)
    ElMessage.success('已删除')
    loadDefs()
  } catch (_) {}
}
</script>

<template>
  <div class="doc-page">
    <PageHeader
      title="测试用例 Test Cases"
      subtitle="管理自动化测试用例工程，支持编辑、分类与启用状态"
      color="app-yellow"
    />

    <div class="doc-body">
      <section class="doc-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            用例工程
            <span class="doc-tag">Definitions</span>
          </h3>
          <AnimalButton type="primary" @click="create">+ 新建用例</AnimalButton>
        </div>
        <div class="doc-section__label">{{ definitions.length }} 个用例定义</div>

        <!-- Category filter tabs + table -->
        <Tabs
          class="case-tabs"
          :items="filterTabs"
          v-model="activeFilter"
          :leaf-animation="true"
          :shadow="true"
        >
          <template v-for="tab in filterTabs" #[tab.key] :key="tab.key">
            <Card color="brown" pattern="brown" class="table-card">
              <Table
                :columns="columns"
                :data-source="filteredDefs"
                row-key="id"
                :striped="true"
                :loading="loading"
                empty-text="暂无用例定义"
                class="case-table"
              >
                <template #cell-enabled="{ value }">
                  <el-tag :type="value ? 'success' : 'info'" effect="dark" size="small" round>
                    {{ value ? '启用' : '停用' }}
                  </el-tag>
                </template>
                <template #cell-actions="{ record }">
                  <div class="action-cell">
                    <AnimalButton size="small" type="primary" @click="edit(record)">编辑</AnimalButton>
                    <AnimalButton size="small" type="danger" plain @click="remove(record)">删除</AnimalButton>
                  </div>
                </template>
                <template #empty>
                  <div class="table-empty">
                    <span>📋</span>
                    <p>暂无用例定义</p>
                    <AnimalButton size="small" type="primary" @click="create">创建第一个用例</AnimalButton>
                  </div>
                </template>
              </Table>
            </Card>
          </template>
        </Tabs>
      </section>
    </div>
  </div>
</template>

<style scoped>
.case-tabs :deep(.animal-tabs__content) {
  padding-top: 16px;
}
.table-card {
  overflow: hidden;
}
.table-card :deep(.animal-card__content) {
  padding: 0;
  border-radius: 14px;
  overflow: hidden;
}

/* Table styles */
.case-table {
  width: 100%;
}
.case-table :deep(table) {
  width: 100%;
  border-collapse: collapse;
}
.case-table :deep(th) {
  font-size: 13px;
  font-weight: 700;
  color: #6b5b48;
  padding: 14px 16px;
  text-align: left;
  background: rgba(139, 115, 85, 0.06);
  border-bottom: 2px solid rgba(139, 115, 85, 0.12);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
.case-table :deep(td) {
  padding: 12px 16px;
  font-size: 14px;
  color: #4A3A28;
  border-bottom: 1px solid rgba(139, 115, 85, 0.06);
  vertical-align: middle;
}
.case-table :deep(tr:hover td) {
  background: rgba(139, 115, 85, 0.03);
}
.case-table :deep(tr:last-child td) {
  border-bottom: none;
}

/* Zebra striping */
.case-table :deep(tr:nth-child(even) td) {
  background: rgba(139, 115, 85, 0.02);
}
.case-table :deep(tr:nth-child(even):hover td) {
  background: rgba(139, 115, 85, 0.04);
}

/* Action buttons */
.action-cell {
  display: flex;
  gap: 8px;
  justify-content: center;
}

/* Empty state */
.table-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 24px;
  color: #988B7A;
}
.table-empty span { font-size: 36px; }
.table-empty p { font-size: 15px; margin: 0; }
</style>
