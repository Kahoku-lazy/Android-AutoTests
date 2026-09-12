<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import KpiCard from '@/shared/components/KpiCard.vue'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import TaskAttemptCard from './components/TaskAttemptCard.vue'
import { ROUTE_AI_ASSISTANT, taskStatusLabel, taskStatusTone } from './constants'
import { useTaskDetail } from './composables/useTaskDetail'
import {
  currentStepLabel,
  defaultStepIndex,
  formatTaskDuration,
  formatTaskTime,
  planGoalText,
  stepBadgeText,
  stepTagClass,
  taskPassCount,
  taskStepBlocks,
} from './helpers/task-detail'

const route = useRoute()
const router = useRouter()
const { loading, error, detail, retry, bindRouteId } = useTaskDetail()

const taskId = computed(() => Number(route.params.taskId))
bindRouteId(taskId)

const blocks = computed(() => taskStepBlocks(detail.value))
const run = computed(() => detail.value?.run || {})
const models = computed(() => run.value.models || {})
const maxLoops = computed(() => models.value.max_loops || run.value.max_loops || 3)
const selectedIndex = ref(0)
const userPicked = ref(false)

watch(
  blocks,
  (list) => {
    if (!list.length) {
      selectedIndex.value = 0
      return
    }
    if (!userPicked.value) {
      selectedIndex.value = defaultStepIndex(list)
      return
    }
    if (selectedIndex.value >= list.length) {
      selectedIndex.value = list.length - 1
    }
  },
  { immediate: true },
)

const selected = computed(() => blocks.value[selectedIndex.value] || null)

function pickStep(i: number) {
  userPicked.value = true
  selectedIndex.value = i
}

function goBack() {
  router.push(`${ROUTE_AI_ASSISTANT}/agents`)
}

const finalToneClass = computed(() => {
  const tone = taskStatusTone(detail.value?.status || '')
  if (tone === 'success') return 'is-ok'
  if (tone === 'failed') return 'is-bad'
  return ''
})
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell ai-workbench task-detail-page">
    <WorkbenchHeader
      title="任务详情"
      :subtitle="detail?.title || detail?.goal || '逐步执行过程'"
      icon="clipboard-list"
      icon-gradient="linear-gradient(135deg, var(--c-ai), #c084fc)"
    >
      <template #actions>
        <el-button class="wb-btn" @click="goBack">返回任务列表</el-button>
      </template>
    </WorkbenchHeader>

    <ErrorState v-if="error" :message="error" @retry="retry" />

    <div v-else v-loading="loading" class="doc-body td-page">
      <template v-if="detail">
        <!-- 上区可滚动：概要 + KPI + 步骤分栏 -->
        <div class="td-main">
          <div class="td-top">
            <div class="td-top__row">
              <span class="task-card__status" :class="`is-${taskStatusTone(detail.status)}`">
                {{ taskStatusLabel(detail.status) }}
              </span>
              <p class="td-top__goal">{{ planGoalText(detail) || detail.goal }}</p>
            </div>
            <p class="td-top__meta">
              <span v-if="detail.device_serial">{{ detail.device_serial }}</span>
              <span v-if="detail.started_at"> · {{ formatTaskTime(detail.started_at) }}</span>
              <span v-if="detail.finished_at"> → {{ formatTaskTime(detail.finished_at) }}</span>
              <span v-if="models.planner || models.executor || models.verifier">
                · {{ models.planner || '—' }} / {{ models.executor || '—' }} / {{ models.verifier || '—' }}
              </span>
            </p>
          </div>

          <div class="td-kpi">
            <KpiCard :value="taskPassCount(blocks)" label="步骤进度" color="var(--c-ai)" shape="diamond" />
            <KpiCard :value="currentStepLabel(blocks)" label="当前步骤" color="var(--c-device)" shape="square" />
            <KpiCard
              :value="formatTaskDuration(detail.started_at, detail.finished_at)"
              label="总耗时"
              color="var(--c-dashboard)"
              shape="triangle"
            />
            <KpiCard
              :value="taskStatusLabel(detail.status)"
              label="任务状态"
              color="var(--c-element)"
              shape="circle"
            />
          </div>

          <div v-if="blocks.length" class="td-split">
            <aside class="td-steps">
              <h4 class="td-split__title">步骤清单</h4>
              <button
                v-for="(b, i) in blocks"
                :key="b.index"
                type="button"
                class="td-step-item"
                :class="[`is-${b.phase}`, { 'is-active': i === selectedIndex }]"
                @click="pickStep(i)"
              >
                <span class="td-step-item__idx">#{{ b.index }}</span>
                <span class="td-step-item__action">{{ b.action }}</span>
                <span class="td-tag" :class="stepTagClass(b.phase)">
                  {{ stepBadgeText(b, maxLoops) }}
                </span>
              </button>
            </aside>

            <section class="td-panel">
              <h4 class="td-split__title">步骤详情</h4>
              <template v-if="selected">
                <div class="td-panel__card">
                  <p><b>操作</b>：{{ selected.action }}</p>
                  <p><b>断言</b>：{{ selected.assert || '—' }}</p>
                  <p class="td-panel__status">
                    状态
                    <span class="td-tag" :class="stepTagClass(selected.phase)">
                      {{ stepBadgeText(selected, maxLoops) }}
                    </span>
                  </p>
                </div>

                <div v-if="selected.attempts.length" class="td-attempts">
                  <TaskAttemptCard
                    v-for="a in selected.attempts"
                    :key="a.loop"
                    :attempt="a"
                    :max-loops="maxLoops"
                  />
                </div>
                <EmptyState
                  v-else-if="selected.phase === 'running'"
                  icon="⏳"
                  text="执行中"
                  hint="完成后会自动刷新本步结果"
                />
                <EmptyState
                  v-else
                  icon="📝"
                  text="等待执行"
                  hint="轮到该步骤时会显示执行与验收结果"
                />
              </template>
            </section>
          </div>
          <EmptyState
            v-else
            icon="📋"
            :text="detail.status === 'running' ? '规划进行中' : '暂无步骤'"
            :hint="detail.status === 'running' ? '规划完成后会列出逐步清单' : '旧任务可能只有摘要，新任务会记录逐步日志'"
          />
        </div>

        <!-- 底栏固定：始终在页面最下方，不叠在步骤区上 -->
        <footer class="td-footer">
          <h4 class="td-h">最终结果</h4>
          <div class="td-final">
            <p :class="finalToneClass">{{ run.summary || run.reason || run.message || '暂无摘要' }}</p>
            <p v-if="run.completed?.length" class="td-meta is-ok">已完成 {{ run.completed.length }} 项</p>
            <p v-if="run.failed?.length" class="td-meta is-bad">
              失败：
              <template v-for="(f, i) in run.failed" :key="i">
                {{ f.action || f.item || '步骤' }}
                <template v-if="f.actual || f.reason">（{{ f.actual || f.reason }}）</template>
                <template v-if="i < (run.failed?.length || 0) - 1">；</template>
              </template>
            </p>
            <p v-if="detail.input_tokens || detail.output_tokens" class="td-meta">
              token 输入 {{ detail.input_tokens || 0 }} · 输出 {{ detail.output_tokens || 0 }}
              <template v-if="detail.cache_input_tokens"> · 缓存命中 {{ detail.cache_input_tokens }}</template>
              <template v-if="detail.deepseek_cost != null">
                · 费用 {{ Number(detail.deepseek_cost).toFixed(4) }} 元
              </template>
            </p>
          </div>
        </footer>
      </template>
    </div>
  </div>
</template>

<style scoped>
/*
  布局契约（钉底栏）：
  task-detail-page(100%高) → td-page(占满剩余) → td-main(唯一滚动) + td-footer(shrink 0)
  禁止步骤区再用 70vh 把最终结果顶到视口中部叠层。
*/
.task-detail-page.doc-page {
  display: flex;
  flex-direction: column;
  height: 100% !important;
  min-height: 0;
  overflow: hidden !important;
}
.td-page {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
  /* 覆盖全局 .doc-page--fixed .doc-body { overflow-y:auto } */
  overflow: hidden !important;
}
.td-main {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
  padding-bottom: var(--app-space-sm);
}
.td-footer {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  padding-top: var(--app-space-xs);
  border-top: 1.5px dashed var(--ai-warm-border, var(--app-border));
  background: var(--doodle-bg, var(--paper));
}
.td-top {
  background: var(--ai-sticky-bg, var(--app-bg-card));
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-md);
  padding: var(--app-space-md);
  flex-shrink: 0;
}
.td-top__row {
  display: flex;
  align-items: flex-start;
  gap: var(--app-space-sm);
}
.td-top__goal {
  margin: 0;
  font-size: var(--app-size-md);
  font-weight: 800;
  color: var(--ink);
  line-height: 1.4;
}
.td-top__meta {
  margin: var(--app-space-xs) 0 0;
  font-size: var(--app-size-xs);
  color: var(--ai-ink-muted, var(--app-text-secondary));
}
.td-kpi {
  display: grid;
  grid-template-columns: var(--layout-kpi-cols);
  gap: var(--app-space-sm);
  flex-shrink: 0;
}
.td-split {
  display: grid;
  grid-template-columns: minmax(240px, 34%) 1fr;
  gap: var(--app-space-md);
  flex: 1 1 0;
  min-height: 56vh;
  align-items: stretch;
}
.td-split__title {
  margin: 0 0 var(--app-space-sm);
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--ink);
  flex-shrink: 0;
}
.td-steps,
.td-panel {
  background: var(--app-bg-card);
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-md);
  padding: var(--app-space-md);
  min-height: 0;
  max-height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.td-steps {
  gap: var(--app-space-xs);
}
.td-step-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: var(--app-space-sm);
  align-items: center;
  width: 100%;
  text-align: left;
  padding: var(--app-space-sm) var(--app-space-md);
  border: 2px solid transparent;
  border-left: 6px solid var(--app-offline, #999);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  cursor: pointer;
  font-family: inherit;
  flex-shrink: 0;
}
.td-step-item.is-pass { border-left-color: var(--app-status-success); }
.td-step-item.is-fail { border-left-color: var(--app-status-danger); }
.td-step-item.is-running { border-left-color: var(--ai-status-blue-border, var(--c-device)); }
.td-step-item.is-active {
  border-color: var(--ink);
  background: var(--ai-warm-bg, var(--app-bg-muted));
}
.td-step-item__idx {
  font-size: var(--app-size-xs);
  font-weight: 800;
  color: var(--ai-ink-muted, var(--app-text-secondary));
}
.td-step-item__action {
  font-size: var(--app-size-sm);
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.td-panel__card {
  margin-bottom: var(--app-space-md);
  padding: var(--app-space-md);
  background: var(--ai-sticky-bg, var(--app-bg-muted));
  border: 1.5px dashed var(--ai-warm-border, var(--app-border));
  border-radius: var(--app-radius-md);
  flex-shrink: 0;
}
.td-panel__card p {
  margin: 0 0 var(--app-space-xs);
  font-size: var(--app-size-sm);
  color: var(--ai-ink-soft, var(--app-text-secondary));
  line-height: 1.5;
}
.td-panel__card p:last-child { margin-bottom: 0; }
.td-panel__status { display: flex; align-items: center; gap: var(--app-space-sm); }
.td-attempts { display: flex; flex-direction: column; gap: var(--app-space-sm); }
.is-ok { color: var(--app-status-success-text); font-weight: 800; }
.is-bad { color: var(--app-status-danger-text); font-weight: 800; }
.td-tag {
  display: inline-block;
  flex-shrink: 0;
  font-size: var(--app-size-xs);
  font-weight: 800;
  padding: 2px var(--app-space-sm);
  border: 1.5px solid var(--ink);
  border-radius: 3px 6px 3px 6px;
  white-space: nowrap;
}
.td-tag--pass { background: var(--app-status-success-bg); color: var(--app-status-success-text); }
.td-tag--fail { background: var(--app-status-danger-bg); color: var(--app-status-danger-text); }
.td-tag--run { background: var(--ai-status-blue-bg, #e8f4ff); color: var(--ai-status-blue-text, #1d4ed8); }
.td-tag--wait { background: var(--ai-bg-neutral, #f3f4f6); color: var(--ai-ink-muted, #6b7280); }
.td-h {
  margin: 0;
  padding-left: var(--app-space-sm);
  border-left: 4px solid var(--c-ai);
  font-size: var(--app-size-md);
  font-weight: 800;
  color: var(--ink);
}
.td-final {
  background: var(--ai-sticky-bg, var(--app-bg-card));
  border: 2px solid var(--ink);
  border-left: 6px solid var(--c-device);
  border-radius: var(--app-radius-md);
  padding: var(--app-space-md);
  max-height: min(28vh, 220px);
  overflow-y: auto;
}
.td-final p {
  margin: 0 0 var(--app-space-xs);
  font-size: var(--app-size-sm);
  color: var(--ai-ink-soft, var(--app-text-secondary));
  line-height: 1.5;
}
.td-final p:last-child { margin-bottom: 0; }
.td-meta { font-size: var(--app-size-xs); color: var(--ai-ink-muted, var(--app-text-secondary)); }
.td-final .is-ok { color: var(--app-status-success-text); font-weight: 800; }
.td-final .is-bad { color: var(--app-status-danger-text); font-weight: 800; }
.task-card__status {
  flex-shrink: 0;
  font-size: var(--app-size-xs);
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 3px 6px 3px 6px;
  border: 1.5px solid var(--ink);
  white-space: nowrap;
}
.task-card__status.is-pending {
  background: var(--ai-bg-neutral, #f3f4f6);
  color: var(--app-timeline-dot, #6b7280);
  border-color: var(--app-offline, #999);
}
.task-card__status.is-running {
  background: var(--ai-status-blue-bg, #e8f4ff);
  color: var(--ai-status-blue-text, #1d4ed8);
  border-color: var(--ai-status-blue-border, #3b82f6);
}
.task-card__status.is-success {
  background: var(--app-status-success-bg);
  color: var(--app-status-success-text);
  border-color: var(--app-status-success);
}
.task-card__status.is-failed {
  background: var(--app-status-danger-bg);
  color: var(--app-status-danger-text);
  border-color: var(--app-status-danger);
}
.task-card__status.is-cancelled {
  background: var(--ai-bg-neutral, #f3f4f6);
  color: var(--ai-ink-muted, #6b7280);
  border-color: var(--app-offline, #999);
}
.task-card__status.is-paused {
  background: var(--app-status-warning-bg);
  color: var(--ai-hint-orange, #c2410c);
  border-color: var(--app-highlight, #f59e0b);
}
@media (max-width: 768px) {
  .td-kpi { grid-template-columns: 1fr 1fr; }
  .td-split {
    grid-template-columns: 1fr;
    min-height: 0;
  }
  .td-steps { max-height: 220px; }
  .td-final { max-height: 30vh; }
}
</style>
