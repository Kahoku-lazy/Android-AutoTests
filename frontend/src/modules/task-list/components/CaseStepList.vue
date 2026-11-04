<script setup>
/**
 * 任务详情：一条用例的步骤清单。
 *
 * 每条步骤一行：序号 + 动作 + 结果徽标；展开后按「次」分块，
 * 块头是次数标签（可折叠，默认展开），块内依次渲染执行过程与验收过程。
 */
import { computed, ref } from "vue"
import { attemptVerdict, formatDurationMs } from "../helpers/report-steps"
import RoundProcess from "./RoundProcess.vue"

const props = defineProps({
  /** helpers/report-steps 产出的步骤视图 */
  steps: { type: Array, default: () => [] },
  /** 已展开的步骤键（含用例前缀） */
  openKeys: { type: Set, default: () => new Set() },
  /** 折叠键的用例前缀，避免跨用例串号 */
  keyPrefix: { type: String, default: "" },
  taskId: { type: Number, required: true },
})

const emit = defineEmits(["toggle"])

/** 结果徽标配色：未完成 / 未执行与待执行同色 */
const BADGE_CLASS = {
  PASS: "is-pass",
  FAIL: "is-fail",
  未完成: "is-pending",
  未执行: "is-pending",
}

/** 尝试块默认展开：只记录被用户收起的那些，步骤一收起组件卸载即复原 */
const collapsedAttempts = ref(new Set())

const rows = computed(() => props.steps || [])

function stepKey(step) {
  return `${props.keyPrefix}${step.key}`
}

function isOpen(step) {
  return props.openKeys.has(stepKey(step))
}

function bodyId(step) {
  return `flow-step-body-${stepKey(step)}`.replace(/[^A-Za-z0-9_-]/g, "-")
}

function badgeClass(outcome) {
  return BADGE_CLASS[outcome] || "is-pending"
}

/** 步骤行的耗时文案：未结束显示「进行中」，缺失或 0 毫秒不渲染 */
function durationText(step) {
  if (step.running) return "进行中"
  return formatDurationMs(step.durationMs)
}

/** 次数标签配色：该次验收驳回标红，重试标绿，首次为默认色 */
function tagClass(attempt) {
  if (attemptVerdict(attempt) === false) return "is-fail"
  if (attempt.attempt > 1) return "is-retry"
  return ""
}

function attemptKey(step, attempt) {
  return `${step.key}#${attempt.attempt}`
}

function attemptOpen(step, attempt) {
  return !collapsedAttempts.value.has(attemptKey(step, attempt))
}

function attemptBodyId(step, attempt) {
  return `flow-attempt-${stepKey(step)}-${attempt.attempt}`.replace(/[^A-Za-z0-9_-]/g, "-")
}

function toggleAttempt(step, attempt) {
  const key = attemptKey(step, attempt)
  const next = new Set(collapsedAttempts.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  collapsedAttempts.value = next
}

function toggle(step) {
  emit("toggle", stepKey(step))
}
</script>

<template>
  <div class="flow-steps">
    <p v-if="!rows.length" class="flow-steps__empty">这次任务还没有步骤记录</p>

    <article
      v-for="step in rows"
      :key="step.key"
      class="flow-step"
      :class="{ 'is-fail': step.outcome === 'FAIL' }"
    >
      <button
        type="button"
        class="flow-step__title"
        :aria-expanded="isOpen(step)"
        :aria-controls="bodyId(step)"
        @click="toggle(step)"
      >
        <span class="flow-step__mark" aria-hidden="true">{{ isOpen(step) ? "▾" : "▸" }}</span>
        <span class="flow-step__text"
          ><strong>{{ step.seq }}.</strong> {{ step.action }}</span
        >
        <span v-if="durationText(step)" class="flow-step__duration">{{ durationText(step) }}</span>
        <span class="flow-step__badge" :class="badgeClass(step.outcome)">{{ step.outcome }}</span>
      </button>

      <div v-if="isOpen(step)" :id="bodyId(step)" class="flow-step__body">
        <p v-if="!step.attempts.length" class="flow-steps__empty">这一步还没有执行记录</p>

        <div v-for="attempt in step.attempts" :key="attempt.attempt" class="flow-attempt">
          <button
            type="button"
            class="flow-attempt__head"
            :aria-expanded="attemptOpen(step, attempt)"
            :aria-controls="attemptBodyId(step, attempt)"
            @click="toggleAttempt(step, attempt)"
          >
            <span class="flow-attempt__mark" aria-hidden="true">{{
              attemptOpen(step, attempt) ? "▾" : "▸"
            }}</span>
            <span class="flow-attempt__tag" :class="tagClass(attempt)"
              >第{{ attempt.attempt }}次</span
            >
          </button>

          <div
            v-if="attemptOpen(step, attempt)"
            :id="attemptBodyId(step, attempt)"
            class="flow-attempt__body"
          >
            <RoundProcess
              v-for="run in attempt.executor"
              :key="run.roundId"
              kind="executor"
              :round="run.round"
              :task-id="taskId"
            />
            <RoundProcess
              v-for="run in attempt.verifier"
              :key="run.roundId"
              kind="verifier"
              :round="run.round"
              :task-id="taskId"
            />
          </div>
        </div>
      </div>
    </article>
  </div>
</template>

<style src="./CaseStepList.style.css" scoped></style>
