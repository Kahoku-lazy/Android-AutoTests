<script setup>
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { animate } from 'animejs'

const props = defineProps({ element: { type: Object, default: null } })

// ── Idle animation ──
const detailIconRef = ref(null)
const detailTitleRef = ref(null)
let detailAnimeInstances = []

function startDetailAnimation() {
  stopDetailAnimation()
  nextTick(() => {
    if (detailIconRef.value) {
      detailAnimeInstances.push(animate(detailIconRef.value, {
        translateY: [-6, 6],
        duration: 3000,
        loop: true,
        ease: 'inOutSine',
        direction: 'alternate',
      }))
    }
    if (detailTitleRef.value) {
      detailAnimeInstances.push(animate(detailTitleRef.value, {
        opacity: [0.45, 1],
        duration: 3000,
        loop: true,
        ease: 'inOutSine',
        direction: 'alternate',
      }))
    }
  })
}

function stopDetailAnimation() {
  detailAnimeInstances.forEach(inst => { try { inst.pause() } catch (_) {} })
  detailAnimeInstances = []
}

watch(() => props.element, (el) => {
  if (el) {
    stopDetailAnimation()
  } else {
    nextTick(() => startDetailAnimation())
  }
}, { immediate: true })

onUnmounted(() => stopDetailAnimation())
</script>

<template>
  <div class="panel">
    <template v-if="element">
      <h3>XPath 筛选</h3>
      <div class="meta">
        <p><strong>Class:</strong> {{ element.class_name }}</p>
        <p v-if="element.text"><strong>Text:</strong> {{ element.text }}</p>
        <p v-if="element.resource_id"><strong>ID:</strong> {{ element.resource_id }}</p>
        <p v-if="element.content_desc"><strong>Desc:</strong> {{ element.content_desc }}</p>
        <p><strong>Bounds:</strong> {{ element.bounds }}</p>
        <p v-if="element.clickable != null">
          <strong>Clickable:</strong> {{ element.clickable ? '是' : '否' }}
        </p>
      </div>
    </template>
    <template v-else>
      <h3>待定页面</h3>
      <div class="placeholder">
        <span ref="detailIconRef" class="placeholder-icon">📋</span>
        <span ref="detailTitleRef" class="placeholder-label">待定页面</span>
        <p class="hint">选中元素后，此处显示 XPath 筛选信息</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.panel {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #fff);
  
  border-radius: 20px;
  border: 1px solid var(--ink));
  padding: 16px;
  box-shadow: var(--app-shadow-sm, 0 4px 15px rgba(0,0,0,0.02));
  overflow-y: auto;
}
h3 {
  font-size: 14px;
  color: var(--app-text, #3D4A3B);
  margin-bottom: 12px;
  flex-shrink: 0;
}
.meta {
  font-size: 12px;
  line-height: 1.6;
}
.meta p {
  margin-bottom: 6px;
  color: var(--app-text-secondary, #7A8B73);
  word-break: break-all;
}
.meta strong {
  color: var(--app-text, #3D4A3B);
}
.placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 200px;
}
.placeholder-icon {
  font-size: 32px;
  opacity: 0.5;
}
.placeholder-label {
  font-size: 15px;
  font-weight: 500;
  color: #725d42;
}
.hint {
  margin: 0;
  font-size: 12px;
  color: var(--app-text-secondary, #7A8B73);
  opacity: 0.5;
}
</style>
