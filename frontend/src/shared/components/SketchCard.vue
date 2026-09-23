<script setup lang="ts">
/**
 * SketchCard — 共享撕纸入口卡（Hand-Drawn Doodle）
 *
 * 对齐 page-principles 撕纸卡：虚线边 / 近直角 / 硬偏移色阴影 / 色块图标 / 微倾。
 * accent 与 tilt 由父级按列表 index 注入（cycle），组件自身不猜配色。
 */
import { computed, nextTick, onMounted, onUpdated } from "vue"

const props = withDefaults(
  defineProps<{
    title: string
    description?: string
    meta?: string
    /** Lucide 名，须已在 lucide-registry 登记 */
    icon?: string
    /** CSS 色或 var(--c-*) */
    tone?: string
    /** 微倾角度（deg） */
    tilt?: number
    deletable?: boolean
    deleteLabel?: string
  }>(),
  {
    description: "",
    meta: "",
    icon: "layers",
    tone: "var(--c-dashboard)",
    tilt: -1.2,
    deletable: false,
    deleteLabel: "删除",
  },
)

const emit = defineEmits<{
  activate: [e: MouseEvent | KeyboardEvent]
  delete: [e: MouseEvent]
}>()

const rootStyle = computed(() => ({
  "--sketch-accent": props.tone,
  "--sketch-tilt": `${props.tilt}deg`,
}))

function refreshIcons() {
  if (props.icon && window.lucide) window.lucide.createIcons()
}

onMounted(async () => {
  await nextTick()
  refreshIcons()
})

onUpdated(async () => {
  await nextTick()
  refreshIcons()
})

function onActivate(e: MouseEvent | KeyboardEvent) {
  emit("activate", e)
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault()
    onActivate(e)
  }
}

function onDelete(e: MouseEvent) {
  e.stopPropagation()
  emit("delete", e)
}
</script>

<template>
  <article
    class="sketch-card"
    :style="rootStyle"
    role="button"
    tabindex="0"
    @click="onActivate"
    @keydown="onKeydown"
  >
    <button
      v-if="deletable"
      type="button"
      class="sketch-card__kill"
      :title="deleteLabel"
      @click="onDelete"
    >
      ×
    </button>
    <div class="sketch-card__icon" aria-hidden="true">
      <slot name="icon">
        <i :data-lucide="icon"></i>
      </slot>
    </div>
    <h3 class="sketch-card__title">{{ title }}</h3>
    <p v-if="description" class="sketch-card__desc">{{ description }}</p>
    <p v-else class="sketch-card__desc is-muted">暂无描述</p>
    <span v-if="meta" class="sketch-card__pg">{{ meta }}</span>
  </article>
</template>

<style scoped>
.sketch-card {
  --sketch-accent: var(--comp-sketch-accent);
  --sketch-tilt: var(--comp-sketch-tilt);
  position: relative;
  width: 100%;
  min-height: 168px;
  padding: var(--app-space-md) var(--app-space-md) 28px;
  text-align: left;
  cursor: pointer;
  background: #fff;
  border: 2.5px dashed var(--ink);
  border-radius: 2px;
  box-shadow: 4px 4px 0 0 var(--sketch-accent);
  transform: rotate(var(--sketch-tilt));
  transition:
    transform var(--app-duration, 0.2s) var(--app-ease, ease),
    box-shadow var(--app-duration, 0.2s) var(--app-ease, ease);
}

.sketch-card:hover,
.sketch-card:focus-visible {
  transform: rotate(0deg) translate(-1px, -1px);
  box-shadow: 5px 5px 0 0 var(--sketch-accent);
  outline: none;
}

.sketch-card:focus-visible {
  outline: 2px solid var(--app-highlight);
  outline-offset: 3px;
}

.sketch-card__icon {
  width: 34px;
  height: 34px;
  margin-bottom: 10px;
  display: grid;
  place-items: center;
  border: 2.5px solid var(--ink);
  background: var(--sketch-accent);
  color: var(--ink);
}

.sketch-card__icon :deep(svg) {
  width: 16px;
  height: 16px;
  stroke-width: 2.4;
  stroke: var(--ink);
  color: var(--ink);
}

.sketch-card__title {
  margin: 0 0 6px;
  font-size: var(--app-size-md);
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--ink);
}

.sketch-card__desc {
  margin: 0;
  font-size: var(--app-size-sm, 13px);
  line-height: 1.45;
  opacity: 0.88;
  color: var(--ink);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.sketch-card__desc.is-muted {
  font-style: italic;
  opacity: 0.5;
}

.sketch-card__pg {
  position: absolute;
  right: 12px;
  bottom: 10px;
  font-size: var(--app-size-xs, 12px);
  font-weight: 700;
  opacity: 0.45;
  color: var(--ink);
}

.sketch-card__kill {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 26px;
  height: 22px;
  display: grid;
  place-items: center;
  border: 1.5px dashed var(--ink);
  background: transparent;
  color: var(--ink);
  font-size: var(--app-size-xs, 12px);
  font-weight: 800;
  opacity: 0.45;
  cursor: pointer;
}

.sketch-card__kill:hover {
  background: var(--app-marker-red);
  color: #fff;
  opacity: 1;
  border-style: solid;
}

@media (prefers-reduced-motion: reduce) {
  .sketch-card {
    transform: none;
    transition: none;
  }
  .sketch-card:hover,
  .sketch-card:focus-visible {
    transform: none;
  }
}
</style>
