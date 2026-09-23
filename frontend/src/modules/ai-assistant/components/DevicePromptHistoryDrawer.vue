<template>
  <el-drawer
    :model-value="modelValue"
    title="提示词历史记录"
    size="620px"
    @update:model-value="onVisibleChange"
  >
    <div class="dph">
      <p class="dph-hint">
        自动存档只保留最近 {{ keep }} 份；永久存档除非手动删除或被覆盖，否则不会变动。
      </p>

      <EmptyState
        v-if="!loading && !archives.length"
        icon="🗂"
        text="还没有历史存档，保存一次就会出现"
      />
      <ul v-else class="dph-list">
        <li
          v-for="item in archives"
          :key="item.id"
          class="dph-item"
          :class="{ 'dph-item-active': preview?.id === item.id }"
        >
          <div class="dph-item-head">
            <span class="dph-kind" :class="item.kind === 'permanent' ? 'dph-perm' : 'dph-auto'">
              {{ kindLabel(item.kind) }}
            </span>
            <span class="dph-time">{{ formatTime(item) }}</span>
          </div>
          <div class="dph-item-body">
            <span class="dph-size">{{ sizeSummary(item) }}</span>
            <span class="dph-actions">
              <button type="button" class="tb-btn" @click="emit('preview', item.id)">预览</button>
              <button type="button" class="tb-btn tb-btn-primary" @click="emit('restore', item.id)">
                覆盖当前
              </button>
              <button
                v-if="item.kind === 'permanent'"
                type="button"
                class="tb-btn danger"
                @click="emit('remove', item.id)"
              >删除</button>
            </span>
          </div>
        </li>
      </ul>

      <section v-if="preview" class="dph-preview">
        <h4 class="dph-preview-title">存档内容</h4>
        <article v-for="role in PROMPT_ROLES" :key="role.key" class="dph-preview-block">
          <p class="dph-preview-role">{{ role.label }}</p>
          <div class="dph-preview-md" v-html="renderMd(roleText(role.key))" />
        </article>
      </section>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import { renderSkillMarkdown } from '../helpers/skill-markdown'
import { PROMPT_ARCHIVE_KIND_LABELS, PROMPT_AUTO_ARCHIVE_KEEP } from '../constants'
import type { DevicePromptArchive, DevicePromptArchiveKind } from '../api/toolbox'

const props = defineProps<{
  modelValue: boolean
  archives: DevicePromptArchive[]
  loading?: boolean
  preview?: DevicePromptArchive | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'preview', id: number): void
  (e: 'restore', id: number): void
  (e: 'remove', id: number): void
}>()

const PROMPT_ROLES = [
  { key: 'planner' as const, label: '规划模型 Planner' },
  { key: 'executor' as const, label: '执行模型 Executor' },
  { key: 'verifier' as const, label: '验收模型 Verifier' },
]

const keep = PROMPT_AUTO_ARCHIVE_KEEP

function onVisibleChange(value: boolean): void {
  emit('update:modelValue', value)
}

function kindLabel(kind: DevicePromptArchiveKind): string {
  return PROMPT_ARCHIVE_KIND_LABELS[kind] || kind
}

function formatTime(item: DevicePromptArchive): string {
  const raw = item.updated_at || item.created_at || ''
  return raw ? raw.replace('T', ' ').slice(0, 16) : '—'
}

function sizeSummary(item: DevicePromptArchive): string {
  const total =
    (item.planner_length || 0) + (item.executor_length || 0) + (item.verifier_length || 0)
  return total ? '三份共 ' + total + ' 字' : '—'
}

function roleText(key: 'planner' | 'executor' | 'verifier'): string {
  return (props.preview && props.preview[key]) || ''
}

function renderMd(src: string): string {
  return renderSkillMarkdown(src || '_（空）_')
}
</script>

<style src="./DevicePromptHistoryDrawer.style.css" scoped></style>
