<script setup lang="ts">
/**
 * 任务便签 — 胶带=智能体名，正文=任务名/进度/状态
 */
import { computed, onMounted, ref } from 'vue'
import { animate } from 'animejs'
import type { TaskRecord } from '@/shared/types/ai'

const props = defineProps<{
  task: TaskRecord
  rotation?: number
  tapeHue?: string
}>()

const emit = defineEmits<{ open: [task: TaskRecord] }>()

const noteRef = ref(null)
const tapeRef = ref(null)

const title = computed(() => props.task.title || props.task.run_id || '未命名任务')
const agentName = computed(() => props.task.agent_name || '未知智能体')
const status = computed(() => String(props.task.status || 'PENDING').toUpperCase())
const statusClass = computed(() => {
  const s = status.value
  if (s === 'RUNNING') return 'is-running'
  if (s === 'COMPLETED' || s === 'SUCCESS') return 'is-done'
  if (s === 'FAILED' || s === 'ERROR') return 'is-fail'
  if (s === 'STOPPED' || s === 'CANCELLED') return 'is-stop'
  return 'is-pending'
})
const isCaseGen = computed(() => props.task.task_type === 'case_generation')

const statusLabel = computed(() => {
  if (isCaseGen.value) {
    const map = {
      PENDING: '等待中',
      RUNNING: '进行中',
      COMPLETED: '已完成',
      SUCCESS: '已完成',
      FAILED: '失败',
      ERROR: '失败',
    }
    return map[status.value] || status.value
  }
  const map = {
    PENDING: '待执行',
    RUNNING: '执行中',
    COMPLETED: '已完成',
    SUCCESS: '已完成',
    FAILED: '失败',
    ERROR: '失败',
    STOPPED: '已停止',
    CANCELLED: '已取消',
  }
  return map[status.value] || status.value
})
const progress = computed(() => {
  const p = props.task.progress || {}
  const total = Math.max(1, Number(p.total) || 1)
  const current = Math.min(total, Math.max(0, Number(p.current) || 0))
  return { current, total, pct: Math.round((current / total) * 100) }
})
const metaLine = computed(() => {
  if (isCaseGen.value) {
    const typeLabel = props.task.case_type_label || props.task.case_type || '用例'
    const n = (props.task.case_titles || props.task.cases || []).length
    return `${typeLabel} · ${n} 个`
  }
  const device = props.task.device_serial || props.task.device_model || ''
  const n = (props.task.case_titles || props.task.cases || []).length
  const parts = []
  if (device) parts.push(device)
  parts.push(`${n} 用例`)
  return parts.join(' · ')
})

onMounted(() => {
  if (noteRef.value) {
    animate(noteRef.value, {
      opacity: [0, 1],
      translateY: [-14, 0],
      rotate: [props.rotation - 3, props.rotation],
      duration: 480,
      ease: 'outBack(1.4)',
    })
  }
  if (tapeRef.value) {
    animate(tapeRef.value, {
      opacity: [0, 1],
      scaleX: [0.65, 1.04, 1],
      duration: 420,
      delay: 120,
      ease: 'outBack(1.5)',
    })
  }
})

function onEnter() {
  if (!noteRef.value) return
  animate(noteRef.value, {
    rotate: props.rotation + (props.rotation >= 0 ? 1 : -1),
    translateY: -3,
    duration: 260,
    ease: 'outCubic',
  })
}
function onLeave() {
  if (!noteRef.value) return
  animate(noteRef.value, {
    rotate: props.rotation,
    translateY: 0,
    duration: 340,
    ease: 'outElastic(1, 0.55)',
  })
}
</script>

<template>
  <article
    ref="noteRef"
    class="task-sticky"
    :style="{ '--rot': rotation + 'deg' }"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
    @click="emit('open', task)"
  >
    <div ref="tapeRef" class="washi-tape" :class="`tape-${tapeHue}`" :title="agentName">
      {{ agentName }}
    </div>
    <div class="note-body">
      <div class="note-head">
        <h4 class="task-title" :title="title">{{ title }}</h4>
        <span class="status-pill" :class="statusClass">{{ statusLabel }}</span>
      </div>
      <p class="task-meta">{{ metaLine }}</p>
      <div class="progress-wrap">
        <div class="progress-bar">
          <div class="progress-fill" :class="statusClass" :style="{ width: progress.pct + '%' }" />
        </div>
        <span class="progress-text">{{ progress.current }} / {{ progress.total }}</span>
      </div>
      <div class="note-foot">
        <span class="run-id">{{ task.run_id }}</span>
        <span class="hint">查看详情 →</span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.task-sticky {
  position: relative;
  width: 260px;
  padding-top: 14px;
  transform: rotate(var(--rot, -2deg));
  transform-origin: center center;
  will-change: transform;
  cursor: pointer;
}
.note-body {
  background: #fffef8;
  border-radius: 18px;
  padding: 22px 14px 12px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 10px 28px rgba(139, 115, 85, 0.14),
    0 2px 6px rgba(61, 52, 40, 0.06);
  border: 1px solid rgba(196, 181, 160, 0.35);
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 140px;
}
.washi-tape {
  position: absolute;
  top: 2px;
  left: 50%;
  z-index: 3;
  transform: translateX(-50%) rotate(-1deg);
  min-width: 88px;
  max-width: 82%;
  padding: 5px 16px 6px;
  font-size: var(--app-size-xs);
  font-weight: 800;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  box-shadow: 0 2px 8px rgba(61, 52, 40, 0.12);
  clip-path: polygon(
    0 12%, 4% 0, 8% 14%, 12% 0, 16% 12%, 20% 0, 24% 14%, 28% 0, 32% 12%,
    36% 0, 40% 14%, 44% 0, 48% 12%, 52% 0, 56% 14%, 60% 0, 64% 12%, 68% 0,
    72% 14%, 76% 0, 80% 12%, 84% 0, 88% 14%, 92% 0, 96% 12%, 100% 0,
    100% 100%, 96% 88%, 92% 100%, 88% 86%, 84% 100%, 80% 88%, 76% 100%,
    72% 86%, 68% 100%, 64% 88%, 60% 100%, 56% 86%, 52% 100%, 48% 88%,
    44% 100%, 40% 86%, 36% 100%, 32% 88%, 28% 100%, 24% 86%, 20% 100%,
    16% 88%, 12% 100%, 8% 86%, 4% 100%, 0 88%
  );
}
.tape-mint { background: rgba(168, 213, 186, 0.88); color: #2f6b3c; }
.tape-peach { background: rgba(255, 200, 170, 0.88); color: #9a4e2e; }
.tape-sky { background: rgba(170, 210, 240, 0.88); color: #2e5f8a; }
.tape-lilac { background: rgba(210, 190, 240, 0.88); color: #5a3d8a; }
.tape-honey { background: rgba(247, 220, 140, 0.9); color: #7a5a18; }

.note-head {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  justify-content: space-between;
}
.task-title {
  margin: 0;
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--doodle-ink, #2d2d2d);
  line-height: 1.3;
  flex: 1;
  min-width: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.status-pill {
  flex-shrink: 0;
  font-size: var(--app-size-xs);
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 999px;
  background: #efe6d8;
  color: #5c4a35;
}
.status-pill.is-running { background: rgba(136, 157, 240, 0.25); color: #3a4aa0; }
.status-pill.is-done { background: rgba(111, 186, 44, 0.22); color: #3d7a14; }
.status-pill.is-fail { background: rgba(232, 95, 95, 0.18); color: #c43a3a; }
.status-pill.is-stop { background: rgba(152, 139, 122, 0.25); color: #6b5a45; }
.status-pill.is-pending { background: rgba(247, 205, 103, 0.35); color: #8a6a18; }

.task-meta {
  margin: 0;
  font-size: var(--app-size-xs);
  font-weight: 600;
  color: #988b7a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.progress-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}
.progress-bar {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: rgba(139, 115, 85, 0.12);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: var(--app-accent-purple, #b39ef3);
  transition: width 0.35s ease;
}
.progress-fill.is-running { background: #889df0; }
.progress-fill.is-done { background: var(--c-workflow); }
.progress-fill.is-fail { background: #e85f5f; }
.progress-fill.is-pending { background: var(--ai-hint-yellow-border); }
.progress-text {
  font-size: var(--app-size-xs);
  font-weight: 800;
  color: #8a7b68;
  white-space: nowrap;
}
.note-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2px;
  padding-top: 6px;
  border-top: 1px dashed rgba(139, 115, 85, 0.18);
}
.run-id {
  font-size: var(--app-size-xs);
  font-weight: 600;
  color: #b0a38e;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 60%;
}
.hint {
  font-size: var(--app-size-xs);
  font-weight: 800;
  color: #0d7a70;
}
</style>
