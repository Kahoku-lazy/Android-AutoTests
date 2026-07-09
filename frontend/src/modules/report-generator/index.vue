<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { animate, stagger } from 'animejs'
import { Button as AnimalButton, Card, Table, Tabs } from 'animal-island-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import { listRuns, statusLabel, statusBadgeClass, formatTime } from './api.js'

const router = useRouter()

const runs = ref([])
const loading = ref(false)
const activeFilter = ref('all')

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await listRuns()
    if (data.ok) runs.value = data.runs || []
  } catch (_) {}
  loading.value = false
  await nextTick()
  animate('.report-table tbody tr', { opacity: [0, 1], translateY: [16, 0], delay: stagger(40), duration: 380, ease: 'outCubic' })
})

// ── Filter tabs ──
const statusTabs = computed(() => [
  { key: 'all', label: `全部 (${runs.value.length})` },
  { key: 'COMPLETED', label: '已完成' },
  { key: 'FAILED', label: '失败' },
  { key: 'STOPPED', label: '已停止' },
])

const filteredRuns = computed(() => {
  if (activeFilter.value === 'all') return runs.value
  return runs.value.filter(r => r.status === activeFilter.value)
})

// ── Table columns ──
const columns = [
  { title: 'Run ID', dataIndex: 'run_id', width: '200px' },
  { title: '设备', dataIndex: 'device_serial', width: '130px' },
  { title: '用例数', dataIndex: 'case_count', width: '70px', align: 'center' },
  { title: '通过', dataIndex: 'passed', width: '60px', align: 'center' },
  { title: '失败', dataIndex: 'failed', width: '60px', align: 'center' },
  { title: '通过率', dataIndex: 'rate', width: '150px' },
  { title: '状态', dataIndex: 'status', width: '90px', align: 'center' },
  { title: '耗时', dataIndex: 'duration', width: '80px', align: 'center' },
  { title: '时间', dataIndex: 'started_at', width: '150px' },
]

function openReport(run) {
  router.push(`/reports/${encodeURIComponent(run.run_id)}`)
}
</script>

<template>
  <div class="doc-page">
    <PageHeader
      title="测试报告 Test Reports"
      subtitle="查看历史测试执行记录，点击 Run ID 进入详细报告"
      color="app-yellow"
    />

    <div class="doc-body">
      <!-- Filter Tabs -->
      <Tabs
        class="report-tabs"
        :items="statusTabs"
        v-model="activeFilter"
        :leaf-animation="true"
        :shadow="true"
      >
        <template v-for="tab in statusTabs" #[tab.key] :key="tab.key">
          <Card color="brown" pattern="brown" class="table-card">
            <Table
              :columns="columns"
              :data-source="filteredRuns"
              row-key="run_id"
              :striped="false"
              :loading="loading"
              empty-text="暂无执行记录，请先执行测试"
              class="report-table report-table--rainbow"
            >
              <!-- Run ID — clickable link -->
              <template #cell-run_id="{ record }">
                <a class="run-link" @click.prevent="openReport(record)" href="#">
                  <code class="cell-run-id">{{ record.run_id }}</code>
                </a>
              </template>

              <template #cell-device_serial="{ value }">
                <span class="cell-device">{{ value }}</span>
              </template>

              <template #cell-case_count="{ value }">
                <span class="cell-count">{{ value }}</span>
              </template>

              <!-- Passed count — green -->
              <template #cell-passed="{ record }">
                <span class="num-pass">{{ record.passed }}</span>
              </template>

              <!-- Failed count — red -->
              <template #cell-failed="{ record }">
                <span :class="record.failed > 0 ? 'num-fail' : ''">{{ record.failed }}</span>
              </template>

              <!-- Pass rate with progress bar -->
              <template #cell-rate="{ record }">
                <div class="rate-cell">
                  <div class="progress-bar">
                    <div class="p-pass" :style="{ width: record.rate + '%' }"></div>
                    <div v-if="record.failed > 0" class="p-fail" :style="{ width: (100 - record.rate) + '%' }"></div>
                  </div>
                  <span class="rate-text" :class="{ 'rate-ok': record.rate >= 95, 'rate-warn': record.rate >= 80 && record.rate < 95, 'rate-bad': record.rate < 80 }">
                    {{ record.rate }}%
                  </span>
                </div>
              </template>

              <!-- Status badge -->
              <template #cell-status="{ record }">
                <span class="badge" :class="statusBadgeClass(record.status)">{{ statusLabel(record.status) }}</span>
              </template>

              <!-- Time -->
              <template #cell-duration="{ value }">
                <span class="cell-duration">{{ value }}</span>
              </template>
              <template #cell-started_at="{ record }">
                <span class="cell-time">{{ formatTime(record.started_at) }}</span>
              </template>

              <!-- Empty state -->
              <template #empty>
                <div class="table-empty">
                  <span>📋</span>
                  <p>暂无执行记录</p>
                  <p class="sub">请先在执行引擎中运行测试，完成后将自动生成报告</p>
                </div>
              </template>
            </Table>
          </Card>
        </template>
      </Tabs>
    </div>
  </div>
</template>

<style scoped>
.doc-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.doc-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.report-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.report-tabs :deep(.animal-tabs) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.report-tabs :deep(.animal-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  display: block;
  padding-top: 16px;
}

.report-tabs :deep(.animal-tabs__inner) {
  min-height: min-content;
}

/* Table card — zero-padding for edge-to-edge Table */
.table-card { overflow: hidden; border-radius: 16px; }
.table-card :deep(.animal-card__content) { padding: 0; border-radius: 16px; overflow: hidden; }

/* Rainbow gradient table */
.report-table { width: 100%; }
.report-table :deep(table) {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.report-table--rainbow :deep(th) {
  font-size: 11px;
  font-weight: 800;
  padding: 13px 12px;
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  white-space: nowrap;
  border: none;
}
.report-table--rainbow :deep(th:nth-child(1)) {
  background: linear-gradient(135deg, #f8a6b2 0%, #e85f5f 100%);
  color: #fff;
}
.report-table--rainbow :deep(th:nth-child(2)) {
  background: linear-gradient(135deg, #ffd97a 0%, #f7cd67 45%, #f5a623 100%);
  color: #5c3d10;
}
.report-table--rainbow :deep(th:nth-child(3)) {
  background: linear-gradient(135deg, #d4e87a 0%, #c5db5a 100%);
  color: #3d5010;
  text-align: center;
}
.report-table--rainbow :deep(th:nth-child(4)) {
  background: linear-gradient(135deg, #9ed456 0%, #6fba2c 100%);
  color: #1e4010;
  text-align: center;
}
.report-table--rainbow :deep(th:nth-child(5)) {
  background: linear-gradient(135deg, #ff8a8a 0%, #e85f5f 100%);
  color: #fff;
  text-align: center;
}
.report-table--rainbow :deep(th:nth-child(6)) {
  background: linear-gradient(135deg, #7ee8df 0%, #19c8b9 100%);
  color: #064a44;
}
.report-table--rainbow :deep(th:nth-child(7)) {
  background: linear-gradient(135deg, #a8b8ff 0%, #889df0 100%);
  color: #2a3568;
  text-align: center;
}
.report-table--rainbow :deep(th:nth-child(8)) {
  background: linear-gradient(135deg, #d4c4ff 0%, #b39ef3 100%);
  color: #3d2d6b;
  text-align: center;
}
.report-table--rainbow :deep(th:nth-child(9)) {
  background: linear-gradient(135deg, #f5c6a3 0%, #f7a8c4 100%);
  color: #6b3d28;
}

.report-table--rainbow :deep(td) {
  padding: 11px 12px;
  font-size: 14px;
  color: #4a3a28;
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(139, 115, 85, 0.08);
  vertical-align: middle;
}
.report-table--rainbow :deep(tr:nth-child(even) td) {
  background: rgba(139, 115, 85, 0.03);
}
.report-table--rainbow :deep(tr:hover td) {
  background: rgba(25, 200, 185, 0.06);
}
.report-table--rainbow :deep(tr:last-child td) {
  border-bottom: none;
}
.report-table--rainbow :deep(td:nth-child(3)),
.report-table--rainbow :deep(td:nth-child(4)),
.report-table--rainbow :deep(td:nth-child(5)),
.report-table--rainbow :deep(td:nth-child(7)),
.report-table--rainbow :deep(td:nth-child(8)) {
  text-align: center;
}

/* Run ID link */
.run-link {
  text-decoration: none;
  color: inherit;
}
.run-link:hover .cell-run-id {
  color: #19c8b9;
  text-decoration: underline;
}
.cell-run-id {
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace;
  font-size: 11px;
  font-weight: 600;
  color: #c0392b;
  line-height: 1.4;
  word-break: break-all;
  transition: color 0.15s ease;
}
.cell-device {
  font-family: 'SF Mono', 'Fira Code', Consolas, monospace;
  font-size: 12px;
  font-weight: 600;
  color: #b8860b;
}
.cell-count {
  font-weight: 700;
  font-size: 14px;
  color: #6b8f1a;
}
.cell-duration {
  font-size: 12px;
  font-weight: 600;
  color: #7b5fbf;
  white-space: nowrap;
}
.cell-time {
  font-size: 12px;
  font-weight: 600;
  color: #b06b48;
  white-space: nowrap;
}

/* Pass/Fail numbers */
.num-pass { color: #4a8c1c; font-weight: 700; }
.num-fail { color: #c0392b; font-weight: 700; }

/* Rate cell */
.rate-cell { display: flex; align-items: center; gap: 10px; }
.progress-bar {
  display: flex; height: 8px; border-radius: 50px; overflow: hidden;
  background: #f0ece2; flex: 1; max-width: 100px;
}
.p-pass { background: #6fba2c; transition: width 0.5s ease; border-radius: 50px; }
.p-fail { background: #e05a5a; transition: width 0.5s ease; border-radius: 50px; }
.rate-text { font-weight: 700; font-size: 13px; min-width: 42px; text-align: right; }
.rate-ok { color: #4a8c1c; }
.rate-warn { color: #b8860b; }
.rate-bad { color: #c0392b; }

/* Status badges */
.badge { display: inline-flex; align-items: center; padding: 4px 12px; border-radius: 50px; font-size: 11px; font-weight: 700; letter-spacing: 0.02em; }
.badge-pass { background: rgba(111,186,44,0.12); color: #4a8c1c; border: 1.5px solid rgba(111,186,44,0.25); }
.badge-fail { background: rgba(224,90,90,0.12); color: #c0392b; border: 1.5px solid rgba(224,90,90,0.25); }
.badge-running { background: rgba(245,195,28,0.12); color: #b8860b; border: 1.5px solid rgba(245,195,28,0.25); }
.badge-stopped { background: rgba(138,123,102,0.10); color: #8a7b66; border: 1.5px solid rgba(138,123,102,0.20); }

/* Empty state */
.table-empty { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 48px 24px; color: #988b7a; }
.table-empty span { font-size: 36px; }
.table-empty p { font-size: 15px; margin: 0; }
.table-empty .sub { font-size: 13px; color: #b8a898; }
</style>
