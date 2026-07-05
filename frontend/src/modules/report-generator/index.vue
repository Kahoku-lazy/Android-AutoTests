<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { animate, stagger } from 'animejs'
import client from '@/shared/api-client.js'
import { Button as AnimalButton, Card, Table, Tabs } from 'animal-island-vue'
import PageHeader from '@/shared/components/PageHeader.vue'

const reports = ref([])
const runs = ref([])
const loading = ref(false)
const viewing = ref(null)  // { name, type, content, rows, headers }
const viewLoading = ref(false)
const activeFilter = ref('all')

onMounted(async () => {
  loading.value = true
  try {
    const [r1, r2] = await Promise.all([client.get('/reports'), client.get('/runner/runs')])
    if (r1.data.ok) reports.value = r1.data.files
    if (r2.data.ok) runs.value = r2.data.runs
  } catch (_) {}
  loading.value = false
  await nextTick()
  animate('.report-table tbody tr', { opacity: [0, 1], translateY: [16, 0], delay: stagger(40), duration: 380, ease: 'outCubic' })
})

// ── Report type filter tabs ──
const reportTypes = computed(() => {
  const types = [...new Set(reports.value.map(r => {
    const ext = r.name.split('.').pop()?.toLowerCase()
    return ['csv', 'json', 'txt', 'log', 'html'].includes(ext) ? ext : 'other'
  }))]
  return [
    { key: 'all', label: `全部 (${reports.value.length})` },
    ...types.map(t => ({ key: t, label: t.toUpperCase() })),
  ]
})

const filteredReports = computed(() => {
  if (activeFilter.value === 'all') return reports.value
  return reports.value.filter(r => {
    const ext = r.name.split('.').pop()?.toLowerCase()
    return ext === activeFilter.value
  })
})

// ── Table column definitions ──
const reportColumns = [
  { title: '文件名', dataIndex: 'name' },
  { title: '大小', dataIndex: 'size', width: '80px' },
  { title: '时间', dataIndex: 'time', width: '170px' },
  { title: '操作', dataIndex: 'actions', width: '140px', align: 'center' },
]

const runColumns = [
  { title: '总数', dataIndex: 'total', width: '60px', align: 'center' },
  { title: '通过', dataIndex: 'passed', width: '60px', align: 'center' },
  { title: '失败', dataIndex: 'failed', width: '60px', align: 'center' },
  { title: '成功率', dataIndex: 'rate', width: '80px', align: 'center' },
  { title: '时间', dataIndex: 'last_time' },
]

const viewerColumns = computed(() => {
  if (!viewing.value || viewing.value.type !== 'csv') return []
  return viewing.value.headers.map(h => ({ title: h, dataIndex: h }))
})

function downloadUrl(name) {
  return `/api/reports/${encodeURIComponent(name)}`
}

async function viewReport(file) {
  viewLoading.value = true
  try {
    const { data } = await client.get(`/reports/${encodeURIComponent(file.name)}/content`)
    if (data.ok) {
      viewing.value = {
        name: data.name,
        type: data.type,
        content: data.content,
        rows: data.rows || [],
        headers: data.headers || [],
      }
    }
  } catch (_) {}
  viewLoading.value = false
}

function closeView() { viewing.value = null }

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}
</script>

<template>
  <div class="doc-page">
    <PageHeader
      title="测试报告 Test Reports"
      subtitle="查看历史测试报告文件与执行统计，支持在线预览与下载"
      color="app-yellow"
    />

    <div class="doc-body">
      <!-- Report Files -->
      <section class="doc-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            报告文件
            <span class="doc-tag">Files</span>
          </h3>
        </div>
        <div class="doc-section__label">已生成的测试报告 ({{ filteredReports.length }})</div>

        <Tabs
          class="report-tabs"
          :items="reportTypes"
          v-model="activeFilter"
          :leaf-animation="true"
          :shadow="true"
        >
          <template v-for="tab in reportTypes" #[tab.key] :key="tab.key">
            <Card color="brown" pattern="brown" class="table-card">
              <Table
                :columns="reportColumns"
                :data-source="filteredReports"
                row-key="name"
                :striped="true"
                :loading="loading"
                empty-text="暂无报告，执行测试后自动生成"
                class="report-table"
              >
                <template #cell-size="{ record }">
                  {{ formatSize(record.size) }}
                </template>
                <template #cell-actions="{ record }">
                  <div class="action-cell">
                    <AnimalButton size="small" type="primary" @click="viewReport(record)">查看</AnimalButton>
                    <a :href="downloadUrl(record.name)" download class="dl-link">下载</a>
                  </div>
                </template>
                <template #empty>
                  <div class="table-empty">
                    <span>📋</span>
                    <p>暂无报告，执行测试后自动生成</p>
                  </div>
                </template>
              </Table>
            </Card>
          </template>
        </Tabs>
      </section>

      <!-- Run History -->
      <section class="doc-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            执行历史
            <span class="doc-tag">History</span>
          </h3>
        </div>
        <div class="doc-section__label">历次任务执行统计 ({{ runs.length }})</div>

        <Card color="brown" pattern="brown" class="table-card">
          <Table
            :columns="runColumns"
            :data-source="runs"
            row-key="last_time"
            :striped="true"
            :loading="loading"
            empty-text="暂无执行记录"
            class="report-table"
          >
            <template #cell-rate="{ record }">
              {{ record.total ? (record.passed / record.total * 100).toFixed(0) + '%' : '—' }}
            </template>
            <template #empty>
              <div class="table-empty">
                <span>🏃</span>
                <p>暂无执行记录</p>
              </div>
            </template>
          </Table>
        </Card>
      </section>
    </div>

    <!-- Inline viewer overlay -->
    <div v-if="viewing" class="viewer-overlay" @click.self="closeView">
      <div class="viewer-panel">
        <div class="viewer-header">
          <h3>{{ viewing.name }}</h3>
          <div class="viewer-header-actions">
            <a :href="downloadUrl(viewing.name)" download class="dl-btn">⬇ 下载</a>
            <AnimalButton size="small" @click="closeView">✕ 关闭</AnimalButton>
          </div>
        </div>

        <!-- CSV table view -->
        <div v-if="viewing.type === 'csv' && viewing.rows.length" class="viewer-body">
          <Table
            :columns="viewerColumns"
            :data-source="viewing.rows"
            :striped="true"
            :loading="viewLoading"
            class="report-table"
          />
        </div>

        <!-- Text / log view -->
        <div v-else class="viewer-body">
          <pre class="viewer-text">{{ viewing.content }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.doc-page { display: flex; flex-direction: column; height: 100%; }

.report-tabs :deep(.animal-tabs__content) {
  padding-top: 16px;
}

/* Table card wrapper — remove default card padding so Table fills edge-to-edge */
.table-card {
  overflow: hidden;
}
.table-card :deep(.animal-card__content) {
  padding: 0;
  border-radius: 14px;
  overflow: hidden;
}

/* Shared Table styles (animal-island brown theme) */
.report-table {
  width: 100%;
}
.report-table :deep(table) {
  width: 100%;
  border-collapse: collapse;
}
.report-table :deep(th) {
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
.report-table :deep(td) {
  padding: 12px 16px;
  font-size: 14px;
  color: #4a3a28;
  border-bottom: 1px solid rgba(139, 115, 85, 0.06);
  vertical-align: middle;
}
.report-table :deep(tr:hover td) {
  background: rgba(139, 115, 85, 0.03);
}
.report-table :deep(tr:last-child td) {
  border-bottom: none;
}

/* Zebra striping */
.report-table :deep(tr:nth-child(even) td) {
  background: rgba(139, 115, 85, 0.02);
}
.report-table :deep(tr:nth-child(even):hover td) {
  background: rgba(139, 115, 85, 0.04);
}

/* Action buttons row */
.action-cell {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
}
.dl-link {
  font-size: 13px;
  color: var(--accent-blue);
  text-decoration: none;
  padding: 4px 8px;
  border-radius: 4px;
}
.dl-link:hover {
  background: rgba(64, 158, 255, 0.1);
}

/* Empty state */
.table-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 24px;
  color: #988b7a;
}
.table-empty span { font-size: 36px; }
.table-empty p { font-size: 15px; margin: 0; }

/* ── Viewer overlay ── */
.viewer-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0, 0, 0, 0.5); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
}
.viewer-panel {
  width: 90vw; max-width: 1100px; max-height: 85vh;
  background: var(--animal-bg-color, #f8f8f0); backdrop-filter: blur(20px);
  border-radius: 20px; border: 1px solid var(--glass-border);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex; flex-direction: column; overflow: hidden;
}
.viewer-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 20px; border-bottom: 1px solid var(--glass-border);
  flex-shrink: 0;
}
.viewer-header h3 { margin: 0; font-size: 16px; }
.viewer-header-actions {
  display: flex; align-items: center; gap: 12px;
}
.viewer-body {
  flex: 1; overflow: auto; padding: 16px;
}
.viewer-body .report-table :deep(.animal-card__content) {
  padding: 0;
  border-radius: 0;
}
.viewer-text {
  font-family: 'Cascadia Code', monospace; font-size: 13px;
  line-height: 1.6; white-space: pre-wrap; word-break: break-all;
  margin: 0; color: var(--text-primary);
}
.dl-btn {
  font-size: 13px; color: var(--accent-blue); text-decoration: none;
  font-weight: 500;
}
</style>
