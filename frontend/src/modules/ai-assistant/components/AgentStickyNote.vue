<script setup>
/**
 * 智能体便签 — 和纸胶带 + 轻微倾斜，贴在点阵看板上
 */
import { computed, onMounted, ref } from 'vue'
import { animate } from 'animejs'

const props = defineProps({
  agent: { type: Object, required: true },
  rotation: { type: Number, default: -2 },
  tapeHue: { type: String, default: 'mint' }, // mint | peach | sky | lilac | honey
  pendingModel: { type: String, default: '' },
  confirming: { type: Boolean, default: false },
  testing: { type: Boolean, default: false },
  statusClass: { type: String, default: 'is-success' },
  statusText: { type: String, default: '' },
  modelOptions: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'update:pendingModel',
  'confirm-model',
  'chat',
  'edit',
  'test',
  'delete',
  'select',
])

const noteRef = ref(null)
const tapeRef = ref(null)

const isImageUrl = (av) => av?.startsWith('/api/ai/avatars/') || av?.startsWith('data:image/')
const avatarStyle = computed(() => {
  const av = props.agent.avatar
  if (isImageUrl(av)) return { backgroundImage: `url(${av})` }
  return {}
})
const showEmoji = computed(() => !isImageUrl(props.agent.avatar))
const modelDirty = computed(
  () => !!props.pendingModel && props.pendingModel !== props.agent.model_name,
)

onMounted(() => {
  const note = noteRef.value
  const tape = tapeRef.value
  if (note) {
    animate(note, {
      opacity: [0, 1],
      translateY: [-18, 0],
      rotate: [props.rotation - 4, props.rotation],
      duration: 520,
      ease: 'outBack(1.5)',
    })
  }
  if (tape) {
    animate(tape, {
      opacity: [0, 1],
      scaleX: [0.6, 1.05, 1],
      translateY: [-8, 0],
      duration: 480,
      delay: 160,
      ease: 'outBack(1.6)',
    })
  }
})

function onEnter() {
  const note = noteRef.value
  if (!note) return
  animate(note, {
    rotate: props.rotation + (props.rotation >= 0 ? 1.2 : -1.2),
    translateY: -4,
    duration: 280,
    ease: 'outCubic',
  })
}
function onLeave() {
  const note = noteRef.value
  if (!note) return
  animate(note, {
    rotate: props.rotation,
    translateY: 0,
    duration: 360,
    ease: 'outElastic(1, 0.6)',
  })
}
</script>

<template>
  <article
    ref="noteRef"
    class="sticky-note"
    :style="{ '--rot': rotation + 'deg' }"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
    @click="emit('select', $event)"
  >
    <div
      ref="tapeRef"
      class="washi-tape"
      :class="`tape-${tapeHue}`"
      :title="agent.name"
    >
      {{ agent.name }}
    </div>

    <div class="note-body">
      <div class="note-top">
        <div class="ac-avatar-wrap">
          <div class="ac-avatar" :style="avatarStyle">
            <span v-if="showEmoji">{{ agent.avatar || '🤖' }}</span>
          </div>
          <span class="ac-status-bubble" :class="statusClass">{{ statusText }}</span>
        </div>
        <div class="note-meta">
          <h4 class="note-name" :title="agent.name">{{ agent.name }}</h4>
          <p v-if="agent.description" class="note-desc" :title="agent.description">
            {{ agent.description }}
          </p>
          <div v-if="agent.tags" class="note-tags">
            <span
              v-for="t in String(agent.tags).split(',').filter(Boolean)"
              :key="t"
              class="note-tag"
            >{{ t.trim() }}</span>
          </div>
          <span class="note-tools">{{ agent.tool_count || 0 }} 个工具</span>
        </div>
      </div>

      <div class="model-row" @click.stop>
        <div class="model-row-head">
          <span class="model-provider">{{ agent.model_provider || '模型' }}</span>
          <button
            v-if="modelDirty"
            type="button"
            class="model-save"
            :disabled="confirming"
            @click="emit('confirm-model')"
          >
            {{ confirming ? '保存中…' : '保存模型' }}
          </button>
        </div>
        <el-select
          :model-value="pendingModel || agent.model_name"
          size="small"
          filterable
          allow-create
          default-first-option
          placeholder="选择模型"
          class="model-select"
          @update:model-value="emit('update:pendingModel', $event)"
        >
          <el-option
            v-for="opt in modelOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </div>

      <div class="note-footer" @click.stop>
        <button type="button" class="note-chat" @click.stop="emit('chat')">对话</button>
        <div class="note-tools-row">
          <button type="button" class="note-tool" @click.stop="emit('edit')">配置</button>
          <button type="button" class="note-tool" :disabled="testing" @click.stop="emit('test')">
            {{ testing ? '测试中…' : '测试' }}
          </button>
          <button type="button" class="note-tool danger" @click.stop="emit('delete')">删除</button>
        </div>
      </div>
    </div>
  </article>
</template>

<style scoped>
.sticky-note {
  position: relative;
  width: 300px;
  padding-top: 14px;
  transform: rotate(var(--rot, -2deg));
  transform-origin: center center;
  will-change: transform;
  cursor: default;
}
.note-body {
  position: relative;
  background: var(--ai-sticky-bg);
  border-radius: 18px;
  padding: 22px 14px 14px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 10px 28px rgba(139, 115, 85, 0.16),
    0 2px 6px rgba(61, 52, 40, 0.06);
  border: 1px solid rgba(196, 181, 160, 0.35);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 和纸胶带 — 撕边 */
.washi-tape {
  position: absolute;
  top: 2px;
  left: 50%;
  z-index: 3;
  transform: translateX(-50%) rotate(-1deg);
  min-width: 96px;
  max-width: 82%;
  padding: 6px 20px 7px;
  font-size: var(--app-size-sm);
  font-weight: 800;
  text-align: center;
  color: var(--app-status-success-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  background: rgba(168, 213, 186, 0.88);
  box-shadow: 0 2px 8px rgba(61, 52, 40, 0.14);
  /* 较浅的撕边，避免裁掉文字 */
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
.tape-mint { background: rgba(168, 213, 186, 0.75); color: var(--app-status-success-text); }
.tape-peach { background: rgba(255, 200, 170, 0.78); color: #9a4e2e; }
.tape-sky { background: rgba(170, 210, 240, 0.78); color: #2e5f8a; }
.tape-lilac { background: rgba(210, 190, 240, 0.78); color: #5a3d8a; }
.tape-honey { background: rgba(247, 220, 140, 0.82); color: #7a5a18; }

.note-top {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.ac-avatar-wrap {
  position: relative;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
}
.ac-avatar {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background-size: cover;
  background-position: center;
  background-color: rgba(139, 115, 85, 0.08);
  display: grid;
  place-items: center;
  font-size: var(--app-size-xl);
  border: 2px solid rgba(139, 115, 85, 0.12);
}
.ac-status-bubble {
  position: absolute;
  top: -10px;
  right: -16px;
  z-index: 2;
  padding: 3px 7px 3px;
  border-radius: 12px 12px 12px 4px;
  font-size: var(--app-size-xs);
  font-weight: 800;
  color: #fff;
  box-shadow: 0 3px 10px rgba(61, 52, 40, 0.16);
  pointer-events: none;
  white-space: nowrap;
}
.ac-status-bubble::after {
  content: '';
  position: absolute;
  left: 5px;
  bottom: -4px;
  border-style: solid;
  border-width: 4px 4px 0 0;
  border-color: currentColor transparent transparent transparent;
  filter: brightness(0.92);
}
.ac-status-bubble.is-success { background: linear-gradient(135deg, var(--c-workflow), #5aa31f); }
.ac-status-bubble.is-success::after { border-top-color: var(--app-status-success); }
.ac-status-bubble.is-danger { background: linear-gradient(135deg, #f07878, #e85f5f); }
.ac-status-bubble.is-danger::after { border-top-color: var(--app-error); }
.ac-status-bubble.is-warning { background: linear-gradient(135deg, var(--ai-hint-yellow-border), #e0b52e); color: var(--doodle-ink, #2d2d2d); }
.ac-status-bubble.is-warning::after { border-top-color: var(--c-dashboard); }

.note-meta {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.note-name {
  margin: 0;
  font-size: var(--app-size-md);
  font-weight: 800;
  color: var(--doodle-ink, #2d2d2d);
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.note-desc {
  margin: 0;
  font-size: var(--app-size-sm);
  font-weight: 600;
  color: var(--ai-ink-muted);
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.note-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.note-tag {
  font-size: var(--app-size-xs);
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 999px;
  background: rgba(139, 115, 85, 0.1);
  color: var(--ai-ink-soft);
}
.note-tools {
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--app-ink-muted, #999);
}

.model-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(139, 115, 85, 0.05);
  border: 1px solid rgba(196, 181, 160, 0.28);
}
.model-row-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.model-provider {
  font-size: var(--app-size-xs);
  font-weight: 800;
  color: var(--ai-ink-muted);
  letter-spacing: 0.02em;
}
.model-save {
  border: none;
  border-radius: 8px;
  padding: 3px 10px;
  font-size: var(--app-size-xs);
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
  color: #fff;
  background: linear-gradient(135deg, #6f9fd8, #5e8fca);
}
.model-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.model-select {
  width: 100%;
}
.model-select :deep(.el-select__wrapper) {
  border-radius: 10px !important;
  min-height: 30px;
  box-shadow: none !important;
  background: rgba(255, 255, 255, 0.85) !important;
}

.note-footer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px dashed rgba(139, 115, 85, 0.2);
}
.note-chat {
  height: 34px;
  border: none;
  border-radius: 999px;
  background: var(--app-accent-purple, #b39ef3);
  color: #fff;
  font-size: var(--app-size-sm);
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
  box-shadow: 0 2px 0 var(--ai-teal);
}
.note-chat:hover { filter: brightness(1.05); }
.note-tools-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 6px;
}
.note-tool {
  height: 28px;
  border-radius: 999px;
  border: 1.5px solid rgba(139, 115, 85, 0.18);
  background: var(--ai-sticky-cream);
  color: var(--ai-ink-subtle);
  font-size: var(--app-size-xs);
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
}
.note-tool:hover:not(:disabled) {
  border-color: var(--app-accent-purple, #b39ef3);
  color: var(--ai-teal-text);
}
.note-tool:disabled { opacity: 0.55; cursor: wait; }
.note-tool.danger:hover:not(:disabled) {
  border-color: rgba(232, 95, 95, 0.5);
  color: var(--app-error);
}
</style>
