<script setup>
import { ElMessageBox } from 'element-plus'
import { useElementStore } from '../store'
import { IconTrash } from '@/shared/icons'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'

const store = useElementStore()

// 抓取方式只剩 dump（OCR 链路已下线；历史 ocr 快照按原值兜底显示）
const METHOD_LABELS = { dump: 'Dump', ocr: 'OCR' }

/** 写库级删除：先二次确认（EP 约定：取消以 reject 表示，非错误） */
async function onDelete(snap) {
  try {
    await ElMessageBox.confirm(
      '删除后该快照与其截图 / 缩略图文件不可恢复',
      '删除快照',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  store.deleteSnapshot(snap.id)
}

/** 一键清空：同样先二次确认；确认后调用清空端点一次（不逐条循环删除） */
async function onClearAll() {
  try {
    await ElMessageBox.confirm(
      `将删除全部 ${store.snapshotTotal} 条历史快照及其未被元素定位引用的截图 / 缩略图文件，不可恢复`,
      '清空历史快照',
      { type: 'warning', confirmButtonText: '清空', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  store.clearSnapshots()
}
</script>

<template>
  <el-drawer
    v-model="store.drawerVisible"
    title="检查器快照"
    size="380px"
  >
    <div class="snap-list">
      <!-- 总数来自后端 total；列表最多返回保留上限条，故总数即全部，不存在截断提示 -->
      <div class="snap-meta" data-testid="snapshot-total">
        <span>共 {{ store.snapshotTotal }} 条</span>
        <el-button
          size="small"
          type="danger"
          data-testid="snapshot-clear"
          :disabled="!store.snapshots.length"
          @click="onClearAll"
        >一键清空</el-button>
      </div>
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
            {{ s.package || '—' }} · 元素 {{ s.element_count }}
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
.snap-list { display: flex; flex-direction: column; gap: var(--insp-gap-row); }
.snap-meta {
  display: flex; align-items: center; justify-content: space-between; gap: var(--app-space-sm);
  font-size: var(--app-size-xs); font-weight: 700; color: var(--app-text-secondary);
}
.snap-item {
  display: flex; align-items: center; justify-content: space-between; gap: var(--app-space-sm);
  padding: var(--insp-pad-snap); border: 2px solid var(--ink);
  border-radius: var(--app-radius-sm); background: var(--app-bg-card);
  cursor: pointer; transition: all var(--app-duration-fast);
}
.snap-item:hover { background: var(--app-highlight); }
.snap-main { min-width: 0; }
.snap-title { font-weight: 700; font-size: var(--app-size-sm); }
.snap-sub { font-size: var(--app-size-xs); color: var(--app-text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.snap-time { font-size: var(--app-size-xs); color: var(--app-text-secondary); }
</style>
