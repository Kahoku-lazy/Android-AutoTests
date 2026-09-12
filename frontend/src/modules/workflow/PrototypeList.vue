<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import { usePrototypes } from './composables/usePrototypes'

const router = useRouter()
const { prototypes, loading, creating, error, isEmpty, loadPrototypes, addPrototype, removePrototype } =
  usePrototypes()

const createDialogVisible = ref(false)
const newName = ref('')
const newDesc = ref('')

onMounted(() => {
  loadPrototypes()
})

function openCreateDialog() {
  newName.value = ''
  newDesc.value = ''
  createDialogVisible.value = true
}

async function confirmCreate() {
  const created = await addPrototype(newName.value, newDesc.value)
  if (created) {
    createDialogVisible.value = false
    router.push(`/workflow/prototypes/${created.id}`)
  }
}

function enterPrototype(id: number) {
  router.push(`/workflow/prototypes/${id}`)
}

async function onDelete(id: number, name: string, event: Event) {
  event.stopPropagation()
  try {
    await ElMessageBox.confirm(
      `删除原型「${name}」将同时删除其下全部目录与页面流，此操作不可恢复。`,
      '确认删除原型',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  await removePrototype(id)
}
</script>

<template>
  <div class="proto-list-page">
    <WorkbenchHeader
      title="页面流"
      subtitle="按原型组织目录与页面流编排"
      icon="git-branch"
      :icon-gradient="'linear-gradient(135deg,var(--c-workflow),#b8e4f8)'"
    >
      <template #actions>
        <el-button type="primary" class="wb-btn" @click="openCreateDialog">+ 新建原型</el-button>
      </template>
    </WorkbenchHeader>

    <div v-if="loading" class="proto-list-page__body proto-list-page__body--loading">
      <el-skeleton :rows="4" animated />
    </div>

    <ErrorState v-else-if="error" :message="error" @retry="loadPrototypes" />

    <div v-else class="proto-list-page__body">
      <EmptyState
        v-if="isEmpty"
        icon="📁"
        text="还没有页面流原型"
        hint="创建第一个原型，开始维护目录与页面流"
      >
        <el-button type="primary" @click="openCreateDialog">创建原型</el-button>
      </EmptyState>

      <div v-else class="proto-grid">
        <article
          v-for="item in prototypes"
          :key="item.id"
          class="proto-card"
          role="button"
          tabindex="0"
          @click="enterPrototype(item.id)"
          @keydown.enter.prevent="enterPrototype(item.id)"
        >
          <div class="proto-card__accent" />
          <div class="proto-card__body">
            <h3 class="proto-card__title">{{ item.name }}</h3>
            <p v-if="item.description" class="proto-card__desc">{{ item.description }}</p>
            <p v-else class="proto-card__desc proto-card__desc--muted">暂无描述</p>
            <div class="proto-card__meta">
              <span>{{ item.doc_count }} 个页面流</span>
              <span>{{ item.updated_at?.slice(0, 10) || '—' }}</span>
            </div>
          </div>
          <button
            type="button"
            class="proto-card__delete"
            title="删除原型"
            @click="onDelete(item.id, item.name, $event)"
          >
            删除
          </button>
        </article>
      </div>
    </div>

    <el-dialog
      v-model="createDialogVisible"
      title="新建原型"
      width="440px"
      :close-on-click-modal="false"
    >
      <el-form label-position="top">
        <el-form-item label="原型名称" required>
          <el-input
            v-model="newName"
            maxlength="200"
            placeholder="例如：制冰机 App 主路径"
            @keyup.enter="confirmCreate"
          />
        </el-form-item>
        <el-form-item label="原型描述">
          <el-input
            v-model="newDesc"
            type="textarea"
            :rows="3"
            maxlength="500"
            placeholder="可选，简要说明原型范围"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="confirmCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.proto-list-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.proto-list-page__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--app-space-lg);
}
.proto-list-page__body--loading {
  max-width: 720px;
}
.proto-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--app-space-md);
}
.proto-card {
  position: relative;
  display: flex;
  flex-direction: column;
  border: 2px solid rgba(137, 207, 240, 0.28);
  border-radius: var(--app-radius-lg);
  background: var(--app-bg-card);
  cursor: pointer;
  transition: border-color var(--app-duration) var(--app-ease),
    box-shadow var(--app-duration) var(--app-ease);
  overflow: hidden;
}
.proto-card:hover,
.proto-card:focus-visible {
  border-color: var(--c-workflow);
  box-shadow: var(--app-shadow-sm);
  outline: none;
}
.proto-card__accent {
  height: 4px;
  background: var(--c-workflow);
}
.proto-card__body {
  padding: var(--app-space-md);
  flex: 1;
}
.proto-card__title {
  margin: 0 0 var(--app-space-xs);
  font-size: var(--app-size-md);
  font-weight: 700;
  color: var(--ink);
}
.proto-card__desc {
  margin: 0 0 var(--app-space-sm);
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.proto-card__desc--muted {
  font-style: italic;
}
.proto-card__meta {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-sm);
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}
.proto-card__delete {
  position: absolute;
  top: var(--app-space-sm);
  right: var(--app-space-sm);
  border: 1px solid rgba(137, 207, 240, 0.35);
  background: rgba(137, 207, 240, 0.08);
  color: #e05a5a;
  font-size: var(--app-size-xs);
  padding: 2px var(--app-space-sm);
  border-radius: var(--app-radius-sm);
  cursor: pointer;
}
.proto-card__delete:hover {
  background: rgba(224, 90, 90, 0.12);
}
</style>
