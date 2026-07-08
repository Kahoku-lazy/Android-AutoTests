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
              :striped="true"
              :loading="loading"
              empty-text="暂无执行记录，请先执行测试"
              class="report-table"
            >
              <!-- Run ID — clickable link -->
              <template #cell-run_id="{ record }">
                <a class="run-link" @click.prevent="openReport(record)" href="#">
                  <code>{{ record.run_id }}</code>
                </a>
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
              <template #cell-started_at="{ record }">
                <span class="time-text">{{ formatTime(record.started_at) }}</span>
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
.doc-page { display: flex; flex-direction: column; height: 100%; }

.report-tabs :deep(.animal-tabs__content) {
  padding-top: 16px;
}

/* Table card — zero-padding for edge-to-edge Table */
.table-card { overflow: hidden; }
.table-card :deep(.animal-card__content) { padding: 0; border-radius: 14px; overflow: hidden; }

/* Shared Table styles */
.report-table { width: 100%; }
.report-table :deep(table) { width: 100%; border-collapse: collapse; }
.report-table :deep(th) {
  font-size: 12px; font-weight: 700; color: #6b5b48; padding: 14px 16px;
  text-align: left; background: rgba(139,115,85,0.06);
  border-bottom: 2px solid rgba(139,115,85,0.12);
  text-transform: uppercase; letter-spacing: 0.3px; white-space: nowrap;
}
.report-table :deep(td) {
  padding: 12px 16px; font-size: 14px; color: #4a3a28;
  border-bottom: 1px dashed rgba(196,184,158,0.4); vertical-align: middle;
}
.report-table :deep(tr:hover td) { background: rgba(25,200,185,0.04); }
.report-table :deep(tr:last-child td) { border-bottom: none; }

/* Run ID link */
.run-link { color: var(--primary, #19c8b9); text-decoration: none; font-weight: 600; }
.run-link:hover { text-decoration: underline; color: #11a89b; }
.run-link code { font-family: 'SF Mono','Fira Code','Cascadia Code',Consolas,monospace; font-size: 12px; }

/* Pass/Fail numbers */
.num-pass { color: #6fba2c; font-weight: 700; }
.num-fail { color: #e05a5a; font-weight: 700; }

/* Rate cell */
.rate-cell { display: flex; align-items: center; gap: 10px; }
.progress-bar { display: flex; height: 8px; border-radius: 50px; overflow: hidden; background: #f0ece2; flex: 1; max-width: 100px; }
.p-pass { background: #6fba2c; transition: width 0.5s ease; border-radius: 50px; }
.p-fail { background: #e05a5a; transition: width 0.5s ease; border-radius: 50px; }
.rate-text { font-weight: 700; font-size: 13px; min-width: 42px; text-align: right; }
.rate-ok { color: #6fba2c; }
.rate-warn { color: #dba90e; }
.rate-bad { color: #e05a5a; }

/* Status badges */
.badge { display: inline-flex; align-items: center; padding: 4px 12px; border-radius: 50px; font-size: 11px; font-weight: 700; letter-spacing: 0.02em; }
.badge-pass { background: rgba(111,186,44,0.12); color: #6fba2c; border: 1.5px solid rgba(111,186,44,0.25); }
.badge-fail { background: rgba(224,90,90,0.12); color: #e05a5a; border: 1.5px solid rgba(224,90,90,0.25); }
.badge-running { background: rgba(245,195,28,0.12); color: #dba90e; border: 1.5px solid rgba(245,195,28,0.25); }
.badge-stopped { background: rgba(138,123,102,0.10); color: #8a7b66; border: 1.5px solid rgba(138,123,102,0.20); }

.time-text { font-size: 13px; color: #8a7b66; white-space: nowrap; }

/* Empty state */
.table-empty { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 48px 24px; color: #988b7a; }
.table-empty span { font-size: 36px; }
.table-empty p { font-size: 15px; margin: 0; }
.table-empty .sub { font-size: 13px; color: #b8a898; }
</style>
