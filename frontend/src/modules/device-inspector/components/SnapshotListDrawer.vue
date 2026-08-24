<script setup>
import { useElementStore } from '../store'
import { IconTrash } from '@/shared/icons'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'

const store = useElementStore()

const METHOD_LABELS = { dump: 'Dump', ocr: 'OCR', both: 'Dump+OCR' }

async function onDelete(snap) {
  store.deleteSnapshot(snap.id)
}
</script>

<template>
  <el-drawer
    :model-value="store.drawerVisible"
    title="检查器快照"
    size="380px"
    @update:model-value="(v) => (store.drawerVisible = v)"
  >
    <div class="snap-list">
      <EmptyState
        v-if="!store.snapshots.length"
        text="暂无快照"
        hint="获取成功后自动保存到这里"
      />
      <div
        v-for="s in store.snapshots"
        :key="s.id"
        class="snap-item"
        data-testid="snapshot-item"
        role="button"
        tabindex="0"
        @click="store.viewSnapshot(s.id)"
        @keydown.enter.prevent="store.viewSnapshot(s.id)"
        @keydown.space.prevent="store.viewSnapshot(s.id)"
      >
        <div class="snap-main">
          <div class="snap-title">
            {{ METHOD_LABELS[s.method] || s.method }} · {{ s.serial }}
          </div>
          <div class="snap-sub">
            {{ s.package || '—' }} · 元素 {{ s.element_count }} · OCR {{ s.ocr_count }}
          </div>
          <div class="snap-time">{{ s.created_at ? new Date(s.created_at).toLocaleString() : '' }}</div>
        </div>
        <el-button
          size="small"
          text
          type="danger"
          data-testid="snapshot-delete"
          @click.stop="onDelete(s)"
        >
          <IconTrash :size="14" />
        </el-button>
      </div>
    </div>
  </el-drawer>
</template>

<style scoped>
.snap-list { display: flex; flex-direction: column; gap: 10px; }
.snap-item {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  padding: 10px 12px; border: 2px solid var(--app-ink, #2d2d2d);
  border-radius: 4px 8px 4px 8px; background: var(--app-bg-card);
  cursor: pointer; transition: all 0.12s;
}
.snap-item:hover { background: var(--app-highlight, #FFE066); }
.snap-main { min-width: 0; }
.snap-title { font-weight: 700; font-size: var(--app-size-sm); }
.snap-sub { font-size: var(--app-size-xs); color: var(--app-text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.snap-time { font-size: var(--app-size-xs); color: var(--app-text-secondary); }
</style>
