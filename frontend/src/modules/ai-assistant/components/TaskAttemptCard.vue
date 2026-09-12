<script setup lang="ts">
/**
 * 单轮尝试卡片：执行结果常显；Agent 过程可折叠（默认收起）。
 */
import { computed } from 'vue'
import type { TaskStepAttempt } from '../helpers/task-detail'
import {
  attemptTraceSides,
  toolScreenshotUrl,
  toolTraceLine,
} from '../helpers/task-detail'

const props = defineProps<{
  attempt: TaskStepAttempt
  maxLoops: number
}>()

const sides = computed(() => attemptTraceSides(props.attempt))
</script>

<template>
  <article
    class="tac"
    :class="attempt.verifierResult === 'pass' ? 'is-pass' : 'is-fail'"
  >
    <header class="tac__head">
      <h4 class="tac__title">尝试 {{ attempt.loop }}/{{ maxLoops }}</h4>
      <span
        class="tac__badge"
        :class="attempt.verifierResult === 'pass' ? 'is-ok' : 'is-bad'"
      >
        验收 {{ attempt.verifierResult || '—' }}
      </span>
    </header>

    <!-- 执行结果：常显，不进折叠 -->
    <section class="tac-result" data-testid="attempt-result">
      <h5 class="tac-result__title">执行结果</h5>
      <p class="tac-result__row">
        <span class="tac-result__label">执行</span>
        <span
          class="tac-result__value"
          :class="attempt.executorResult === 'pass' ? 'is-ok' : attempt.executorResult === 'fail' ? 'is-bad' : ''"
        >
          {{ attempt.executorResult || '—' }}
        </span>
        <span v-if="attempt.executorMessage" class="tac-result__msg">
          · {{ attempt.executorMessage }}
        </span>
      </p>
      <p class="tac-result__row">
        <span class="tac-result__label">验收</span>
        <span
          class="tac-result__value"
          :class="attempt.verifierResult === 'pass' ? 'is-ok' : 'is-bad'"
        >
          {{ attempt.verifierResult || '—' }}
        </span>
        <span v-if="attempt.actual" class="tac-result__msg">
          · {{ attempt.actual }}
        </span>
      </p>
      <div v-if="attempt.screenshotUrl" class="tac-result__shot">
        <span class="tac-result__shot-label">验证截图</span>
        <el-image
          :src="attempt.screenshotUrl"
          :preview-src-list="[attempt.screenshotUrl]"
          fit="contain"
          class="tac__img"
          preview-teleported
          data-testid="attempt-screenshot"
        />
      </div>
    </section>

    <!-- Agent 过程：默认全部收起 -->
    <el-collapse v-if="sides.length" class="tac-trace">
      <el-collapse-item
        v-for="side in sides"
        :key="side.key"
        :name="side.key"
        :title="side.label"
      >
        <el-collapse class="tac-trace tac-trace--nested">
          <el-collapse-item
            v-if="side.trace.input"
            :name="`${side.key}-input`"
            title="输入"
          >
            <p class="tac-trace__body">{{ side.trace.input }}</p>
          </el-collapse-item>
          <el-collapse-item
            v-if="side.trace.thinking?.length"
            :name="`${side.key}-think`"
            title="思考过程"
          >
            <p
              v-for="(t, ti) in side.trace.thinking"
              :key="ti"
              class="tac-trace__body"
            >{{ t }}</p>
          </el-collapse-item>
          <el-collapse-item
            v-if="side.trace.tools?.length"
            :name="`${side.key}-tools`"
            title="工具"
          >
            <ul class="tac-trace__tools">
              <li v-for="(tool, ti) in side.trace.tools" :key="ti">
                <span>{{ toolTraceLine(tool) }}</span>
                <el-image
                  v-if="toolScreenshotUrl(tool)"
                  :src="toolScreenshotUrl(tool)"
                  :preview-src-list="[toolScreenshotUrl(tool)]"
                  fit="contain"
                  class="tac__img tac__img--tool"
                  preview-teleported
                />
              </li>
            </ul>
          </el-collapse-item>
          <el-collapse-item
            v-if="side.trace.text"
            :name="`${side.key}-text`"
            title="文本"
          >
            <p class="tac-trace__body">{{ side.trace.text }}</p>
          </el-collapse-item>
        </el-collapse>
      </el-collapse-item>
    </el-collapse>
  </article>
</template>

<style scoped>
.tac {
  padding: var(--app-space-sm) var(--app-space-md);
  border: 1.5px dashed var(--ai-warm-border, var(--app-border));
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
  background: var(--ai-sticky-bg, var(--app-bg-muted));
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
.tac-result__row:last-of-type { margin-bottom: 0; }
.tac-result__label {
  font-weight: 700;
  color: var(--ai-ink-muted, var(--app-text-muted));
  min-width: 2em;
}
.tac-result__value { font-weight: 800; }
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
  border: 1.5px solid var(--ai-warm-border, var(--app-border));
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-subtle, var(--paper));
  cursor: zoom-in;
}
.tac__img--tool {
  max-height: 140px;
  margin-top: var(--app-space-xs);
}
.tac-trace {
  border: none;
}
.tac-trace--nested {
  padding-left: var(--app-space-sm);
}
.tac-trace :deep(.el-collapse-item__header) {
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
  height: auto;
  line-height: 1.4;
  padding: var(--app-space-xs) 0;
  border: none;
  background: transparent;
}
.tac-trace :deep(.el-collapse-item__wrap),
.tac-trace :deep(.el-collapse-item__content) {
  border: none;
  background: transparent;
  padding: 0 0 var(--app-space-xs);
}
.tac-trace :deep(.el-collapse-item) {
  border-left: 2px solid var(--ai-warm-border, var(--app-border));
  padding-left: var(--app-space-sm);
  margin-bottom: var(--app-space-xs);
}
.tac-trace__body {
  margin: 0 0 var(--app-space-xs);
  font-size: var(--app-size-sm);
  font-weight: 400;
  color: var(--ai-ink-soft, var(--app-text-secondary));
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
.tac-trace__tools {
  margin: 0;
  padding-left: 1.2em;
  font-size: var(--app-size-sm);
  color: var(--ai-ink-soft, var(--app-text-secondary));
  line-height: 1.5;
}
.is-ok { color: var(--app-status-success-text); font-weight: 800; }
.is-bad { color: var(--app-status-danger-text); font-weight: 800; }
</style>
