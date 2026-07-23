<script setup lang="ts">
import { ref, computed } from 'vue'
import { getPaletteCategories, type PaletteItem } from '@/modules/workflow/composables/blocklyBlocks'

const emit = defineEmits<{
  addBlock: [type: string]
}>()

const categories = getPaletteCategories()
const openKey = ref(categories[0]?.key || '')
const filter = ref('')

const filteredCats = computed(() => {
  const q = filter.value.trim().toLowerCase()
  if (!q) return categories
  return categories
    .map(c => ({
      ...c,
      items: c.items.filter(
        i => i.label.toLowerCase().includes(q) || (i.hint || '').toLowerCase().includes(q)
      ),
    }))
    .filter(c => c.items.length > 0)
})

function toggle(key: string) {
  openKey.value = openKey.value === key ? '' : key
}

function onBrickClick(item: PaletteItem) {
  emit('addBlock', item.type)
}

function onDragStart(e: DragEvent, item: PaletteItem) {
  e.dataTransfer?.setData('application/x-blockly-type', item.type)
  e.dataTransfer!.effectAllowed = 'copy'
}
</script>

<template>
  <aside class="palette">
    <div class="palette-head">
      <div class="palette-title">积木箱</div>
      <p class="palette-desc">点击或拖到画布添加</p>
      <input v-model="filter" class="palette-search" placeholder="搜索积木…" />
    </div>

    <div class="palette-scroll">
      <section v-for="cat in filteredCats" :key="cat.key" class="cat">
        <button
          type="button"
          class="cat-head"
          :class="{ open: openKey === cat.key }"
          :style="{ '--cat': cat.color, '--cat-deep': cat.accent }"
          @click="toggle(cat.key)"
        >
          <span class="cat-icon">{{ cat.icon }}</span>
          <span class="cat-name">{{ cat.name }}</span>
          <span class="cat-count">{{ cat.items.length }}</span>
          <span class="cat-chevron">{{ openKey === cat.key ? '▾' : '▸' }}</span>
        </button>

        <div v-show="openKey === cat.key" class="cat-body">
          <button
            v-for="item in cat.items"
            :key="item.type"
            type="button"
            class="brick"
            draggable="true"
            :style="{ '--brick': item.color }"
            @click="onBrickClick(item)"
            @dragstart="onDragStart($event, item)"
          >
            <span class="brick-notch" aria-hidden="true" />
            <span class="brick-icon">{{ item.icon }}</span>
            <span class="brick-label">{{ item.label }}</span>
            <span class="brick-plus">+</span>
          </button>
        </div>
      </section>
    </div>
  </aside>
</template>

<style scoped>
.palette {
  width: 232px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-right: 1px solid var(--doodle-ink, #2d2d2d);
  min-height: 0;
}
.palette-head {
  padding: 14px 12px 10px;
  border-bottom: 1px solid rgba(162,210,255,0.18);
}
.palette-title {
  font-size: 15px;
  font-weight: 800;
  color: var(--app-text);
}
.palette-desc {
  margin: 2px 0 10px;
  font-size: 11px;
  color: var(--app-text-secondary);
  font-weight: 600;
}
.palette-search {
  width: 100%;
  padding: 8px 10px;
  border: 1.5px solid var(--doodle-ink, #2d2d2d);
  border-radius: 12px;
  background: rgba(255,255,255,0.48);
  color: var(--app-text);
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  outline: none;
}
.palette-search:focus {
  border-color: var(--app-blue);
}
.palette-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 10px 10px 16px;
}
.cat {
  margin-bottom: 10px;
}
.cat-head {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border: none;
  border-radius: 14px;
  background: var(--cat);
  color: #fff;
  font-family: inherit;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  box-shadow:
    0 3px 0 var(--cat-deep),
    0 4px 10px rgba(74, 58, 40, 0.12);
  transition: transform 0.12s ease;
}
.cat-head:hover {
  transform: translateY(-1px);
}
.cat-head.open {
  border-radius: 14px 14px 8px 8px;
}
.cat-icon {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.22);
  border-radius: 8px;
  font-size: 13px;
}
.cat-name { flex: 1; text-align: left; }
.cat-count {
  font-size: 10px;
  font-weight: 800;
  background: rgba(0, 0, 0, 0.16);
  border-radius: 999px;
  padding: 2px 7px;
}
.cat-chevron { font-size: 11px; opacity: 0.9; }

.cat-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 4px 4px;
}

/* Scratch-like brick chip */
.brick {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px 12px;
  border: none;
  border-radius: 10px 10px 12px 12px;
  background: var(--brick);
  color: #fff;
  font-family: inherit;
  font-size: 12px;
  font-weight: 800;
  cursor: grab;
  text-align: left;
  box-shadow:
    inset 0 2px 0 rgba(255, 255, 255, 0.28),
    0 3px 0 color-mix(in srgb, var(--brick) 75%, #000),
    0 6px 12px rgba(74, 58, 40, 0.14);
  transition: transform 0.12s ease, filter 0.12s ease;
}
.brick:hover {
  transform: translateY(-2px) scale(1.02);
  filter: brightness(1.05);
}
.brick:active {
  cursor: grabbing;
  transform: translateY(1px);
  box-shadow:
    inset 0 2px 0 rgba(255, 255, 255, 0.2),
    0 1px 0 color-mix(in srgb, var(--brick) 75%, #000);
}

/* bottom notch — Scratch connector silhouette */
.brick-notch {
  position: absolute;
  left: 50%;
  bottom: -7px;
  width: 18px;
  height: 10px;
  transform: translateX(-50%);
  background: var(--brick);
  border-radius: 0 0 6px 6px;
  box-shadow: 0 2px 0 color-mix(in srgb, var(--brick) 75%, #000);
  clip-path: polygon(0 0, 100% 0, 80% 100%, 20% 100%);
}
.brick-icon {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.22);
  font-size: 14px;
  flex-shrink: 0;
}
.brick-label { flex: 1; line-height: 1.2; }
.brick-plus {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.28);
  display: grid;
  place-items: center;
  font-size: 14px;
  font-weight: 800;
  opacity: 0.85;
}
</style>
