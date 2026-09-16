<script setup lang="ts">
/**
 * WorkbenchCrumbs — L2 子页可见回退（返回芯片 + 波浪面包屑）
 * 挂在 WorkbenchHeader #nav；祖先可点，末级马克笔且不可点。
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'

export type CrumbItem = {
  label: string
  /** 省略 to 表示当前页（不可点） */
  to?: string
}

const props = withDefaults(
  defineProps<{
    items?: CrumbItem[]
    /** 可选左侧返回芯片目标 */
    backTo?: string
    backLabel?: string
  }>(),
  {
    items: () => [],
    backTo: '',
    backLabel: '返回',
  },
)

const emit = defineEmits<{
  back: []
  navigate: [to: string]
}>()

const router = useRouter()

const crumbs = computed(() => props.items || [])
const showBack = computed(() => Boolean(props.backTo))

function goBack() {
  if (!props.backTo) return
  emit('back')
  void router.push(props.backTo)
}

function goCrumb(item: CrumbItem) {
  if (!item.to) return
  emit('navigate', item.to)
  void router.push(item.to)
}
</script>

<template>
  <nav class="wb-crumbs" aria-label="面包屑">
    <button
      v-if="showBack"
      type="button"
      class="wb-crumbs__back"
      @click="goBack"
    >
      ← {{ backLabel }}
    </button>
    <ol v-if="crumbs.length" class="wb-crumbs__list">
      <li
        v-for="(item, idx) in crumbs"
        :key="`${item.label}-${idx}`"
        class="wb-crumbs__item"
      >
        <span v-if="idx > 0" class="wb-crumbs__sep" aria-hidden="true">/</span>
        <button
          v-if="item.to"
          type="button"
          class="wb-crumbs__link"
          @click="goCrumb(item)"
        >
          {{ item.label }}
        </button>
        <span
          v-else
          class="wb-crumbs__here"
          aria-current="page"
        >{{ item.label }}</span>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
.wb-crumbs {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--comp-crumb-gap, var(--app-space-sm));
  min-width: 0;
  width: 100%;
}

.wb-crumbs__back {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 2px 10px;
  border: 2px solid var(--comp-crumb-ink, var(--ink));
  border-radius: 2px 6px 2px 4px;
  background: var(--comp-crumb-back-bg, var(--app-bg-card));
  box-shadow: var(--comp-crumb-back-shadow, 2px 2px 0 0 var(--ink));
  color: var(--comp-crumb-ink, var(--ink));
  font: inherit;
  font-size: var(--app-size-xs);
  font-weight: 800;
  cursor: pointer;
  line-height: 1.3;
}

.wb-crumbs__back:hover {
  transform: translate(-1px, -1px);
}

.wb-crumbs__back:active {
  transform: translate(1px, 1px);
  box-shadow: 1px 1px 0 0 var(--comp-crumb-ink, var(--ink));
}

.wb-crumbs__list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin: 0;
  padding: 0;
  list-style: none;
  min-width: 0;
}

.wb-crumbs__item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.wb-crumbs__sep {
  color: var(--comp-crumb-muted, var(--app-text-secondary));
  font-weight: 700;
  opacity: 0.45;
}

.wb-crumbs__link {
  border: 0;
  background: transparent;
  padding: 0;
  font: inherit;
  font-size: var(--app-size-xs);
  font-weight: 800;
  color: var(--comp-crumb-ink, var(--ink));
  cursor: pointer;
  text-decoration-line: underline;
  text-decoration-style: wavy;
  text-decoration-color: var(--comp-crumb-wave, var(--c-case));
  text-underline-offset: 3px;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wb-crumbs__here {
  font-size: var(--app-size-xs);
  font-weight: 800;
  color: var(--comp-crumb-ink, var(--ink));
  background: linear-gradient(
    transparent 55%,
    color-mix(in srgb, var(--comp-crumb-marker, var(--c-dashboard)) 72%, transparent) 55%
  );
  padding: 0 0.15em;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (prefers-reduced-motion: reduce) {
  .wb-crumbs__back:hover,
  .wb-crumbs__back:active {
    transform: none;
  }
}
</style>
