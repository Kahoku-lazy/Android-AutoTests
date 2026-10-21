<script setup lang="ts">
/**
 * 单轮尝试卡片：执行结果常显，下接日志检查与设备日志证据。
 */
import { computed } from "vue"
import StepLogCheck from "./StepLogCheck.vue"
import StepLogEvidence from "./StepLogEvidence.vue"
import type { TaskStepAttempt } from "../helpers/task-detail"
import { hasLogCheck } from "../helpers/task-detail"
import { STEP_EXEC_NO_SHOT_TEXT } from "../constants"

const props = defineProps<{
  attempt: TaskStepAttempt
  maxLoops: number
}>()

const showLogCheck = computed(() => hasLogCheck(props.attempt.logCheck))
/** 新执行契约的点击证据（点击前时间戳 / 点击后截图路径）是否有内容可显示 */
const hasExecEvidence = computed(
  () => Boolean(props.attempt.executorClickTimer) || Boolean(props.attempt.executorScreenshotPath),
)
</script>

<template>
  <article class="tac" :class="attempt.verifierResult === 'pass' ? 'is-pass' : 'is-fail'">
    <header class="tac__head">
      <h4 class="tac__title">尝试 {{ attempt.loop }}/{{ maxLoops }}</h4>
      <span class="tac__badge" :class="attempt.verifierResult === 'pass' ? 'is-ok' : 'is-bad'">
        验收 {{ attempt.verifierResult || "—" }}
      </span>
    </header>

    <!-- 执行结果：常显，不进折叠 -->
    <section class="tac-result" data-testid="attempt-result">
      <h5 class="tac-result__title">执行结果</h5>
      <p class="tac-result__row">
        <span class="tac-result__label">执行</span>
        <span
          class="tac-result__value"
          :class="
            attempt.executorResult === 'pass'
              ? 'is-ok'
              : attempt.executorResult === 'fail'
                ? 'is-bad'
                : ''
          "
        >
          {{ attempt.executorResult || "—" }}
        </span>
        <span v-if="attempt.executorMessage" class="tac-result__msg">
          · {{ attempt.executorMessage }}
        </span>
      </p>
      <!-- 新执行契约的两件证据：点击前时间戳 + 点击后截图（没有就不显示该行，不留空壳） -->
      <p v-if="attempt.executorClickTimer" class="tac-result__row">
        <span class="tac-result__label">点击前时间</span>
        <span class="tac-result__msg" data-testid="attempt-executor-click-timer">
          {{ attempt.executorClickTimer }}
        </span>
      </p>
      <p v-if="hasExecEvidence" class="tac-result__row">
        <span class="tac-result__label">点击后截图</span>
        <span
          v-if="attempt.executorScreenshotPath"
          class="tac-result__msg"
          data-testid="attempt-executor-shot-path"
        >
          {{ attempt.executorScreenshotPath }}
        </span>
        <span v-else class="tac-result__msg" data-testid="attempt-executor-shot-none">
          {{ STEP_EXEC_NO_SHOT_TEXT }}
        </span>
      </p>
      <div v-if="attempt.executorScreenshotUrl" class="tac-result__shot">
        <el-image
          :src="attempt.executorScreenshotUrl"
          :preview-src-list="[attempt.executorScreenshotUrl]"
          fit="contain"
          class="tac__img"
          preview-teleported
          data-testid="attempt-executor-screenshot"
        />
      </div>
      <p class="tac-result__row">
        <span class="tac-result__label">验收</span>
        <span
          class="tac-result__value"
          :class="attempt.verifierResult === 'pass' ? 'is-ok' : 'is-bad'"
        >
          {{ attempt.verifierResult || "—" }}
        </span>
        <span v-if="attempt.actual" class="tac-result__msg"> · {{ attempt.actual }} </span>
      </p>
      <!-- 新验收契约的坐标：本轮检查的日志关键词 + 检测到的时间戳（没有就不显示该行） -->
      <p v-if="attempt.verifierLogInfo" class="tac-result__row">
        <span class="tac-result__label">日志断言</span>
        <span class="tac-result__msg" data-testid="attempt-verifier-log-info">
          {{ attempt.verifierLogInfo }}
        </span>
      </p>
      <p v-if="attempt.verifierLogTimer" class="tac-result__row">
        <span class="tac-result__label">日志断言时间</span>
        <span class="tac-result__msg" data-testid="attempt-verifier-log-timer">
          {{ attempt.verifierLogTimer }}
        </span>
      </p>
      <div v-if="attempt.screenshotUrl || attempt.verifierScreenshotPath" class="tac-result__shot">
        <span class="tac-result__shot-label">验证截图</span>
        <span
          v-if="attempt.verifierScreenshotPath"
          class="tac-result__msg"
          data-testid="attempt-verifier-shot-path"
        >
          {{ attempt.verifierScreenshotPath }}
        </span>
        <el-image
          v-if="attempt.screenshotUrl"
          :src="attempt.screenshotUrl"
          :preview-src-list="[attempt.screenshotUrl]"
          fit="contain"
          class="tac__img"
          preview-teleported
          data-testid="attempt-screenshot"
        />
      </div>
    </section>

    <!-- 执行侧点击证据：点击前时间点 + 点击后截图路径（+ 需日志核对时的 5 秒窗口日志） -->
    <StepLogCheck v-if="showLogCheck" :check="attempt.logCheck" />

    <!-- 验收依据：设备日志证据（摘要常显 + 详情折叠） -->
    <StepLogEvidence :evidence="attempt.logEvidence" />
  </article>
</template>

<style scoped>
.tac {
  padding: var(--app-space-sm) var(--app-space-md);
  border: 1.5px dashed var(--ai-warm-border);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
}
.tac.is-pass {
  background: var(--app-status-success-bg);
  border-color: var(--app-status-success);
}
.tac.is-fail {
  background: var(--app-status-danger-bg);
  border-color: var(--app-status-danger);
}
.tac__head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--app-space-sm);
}
.tac__title {
  margin: 0;
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--ink);
  line-height: 1.4;
}
.tac__badge {
  font-size: var(--app-size-xs);
  font-weight: 800;
}
.tac-result {
  padding: var(--app-space-sm);
  border-left: 3px solid var(--ink);
  background: var(--ai-sticky-bg);
  border-radius: 0 var(--app-radius-sm) var(--app-radius-sm) 0;
}
.tac-result__title {
  margin: 0 0 var(--app-space-xs);
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--ink);
  line-height: 1.4;
}
.tac-result__row {
  margin: 0 0 var(--app-space-xs);
  font-size: var(--app-size-sm);
  color: var(--ai-ink-soft, var(--app-text-secondary));
  line-height: 1.5;
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--app-space-xs);
}
.tac-result__row:last-of-type {
  margin-bottom: 0;
}
.tac-result__label {
  font-weight: 700;
  color: var(--ai-ink-muted, var(--app-text-muted));
  min-width: 2em;
}
.tac-result__value {
  font-weight: 800;
}
.tac-result__msg {
  color: var(--ai-ink-soft, var(--app-text-secondary));
  white-space: pre-wrap;
  word-break: break-word;
}
.tac-result__shot {
  margin-top: var(--app-space-sm);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
}
.tac-result__shot-label {
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--ai-ink-muted, var(--app-text-muted));
}
.tac__img {
  width: 100%;
  max-height: 220px;
  border: 1.5px solid var(--ai-warm-border);
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-subtle, var(--paper));
  cursor: zoom-in;
}
.is-ok {
  color: var(--app-status-success-text);
  font-weight: 800;
}
.is-bad {
  color: var(--app-status-danger-text);
  font-weight: 800;
}
</style>
