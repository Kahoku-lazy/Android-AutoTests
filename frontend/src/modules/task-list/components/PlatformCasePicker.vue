<script setup lang="ts">
/**
 * PlatformCasePicker — 新建任务的平台用例选择器（项目 → 用例表 → 用例多选）。
 *
 * 只做选择与展示：数据由 usePlatformCases 加载，选中编号经 v-model 回传父级；
 * 切项目/切表由父级负责清空已选用例。
 */
import { computed } from "vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import type {
  PlatformCaseOption,
  PlatformFileOption,
  PlatformProjectOption,
} from "../composables/usePlatformCases"

const props = defineProps<{
  projects: PlatformProjectOption[]
  files: PlatformFileOption[]
  cases: PlatformCaseOption[]
  projectId: number | null
  fileId: number | null
  caseIds: string[]
  loading: boolean
  error: string
}>()

const emit = defineEmits<{
  "update:projectId": [value: number | null]
  "update:fileId": [value: number | null]
  "update:caseIds": [value: string[]]
}>()

const allChecked = computed({
  get: () => props.cases.length > 0 && props.caseIds.length === props.cases.length,
  set: (checked: boolean) =>
    emit("update:caseIds", checked ? props.cases.map((row) => row.id) : []),
})

const pickedCount = computed(() => props.caseIds.length)
</script>

<template>
  <div class="platform-case-picker">
    <div class="platform-case-picker__selects">
      <el-select
        :model-value="projectId"
        placeholder="选择用例项目"
        clearable
        filterable
        style="width: 100%"
        @update:model-value="emit('update:projectId', $event as number | null)"
      >
        <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select
        :model-value="fileId"
        placeholder="选择用例表"
        clearable
        filterable
        :disabled="projectId === null"
        style="width: 100%"
        @update:model-value="emit('update:fileId', $event as number | null)"
      >
        <el-option v-for="item in files" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
    </div>

    <p v-if="error" class="platform-case-picker__error">{{ error }}</p>

    <div v-loading="loading" class="platform-case-picker__cases">
      <template v-if="cases.length">
        <div class="platform-case-picker__head">
          <el-checkbox v-model="allChecked">全选（{{ cases.length }} 条）</el-checkbox>
          <span class="platform-case-picker__count">已选 {{ pickedCount }} 条</span>
        </div>
        <el-checkbox-group
          :model-value="caseIds"
          class="platform-case-picker__list"
          @update:model-value="emit('update:caseIds', $event as string[])"
        >
          <el-checkbox
            v-for="row in cases"
            :key="row.id"
            :value="row.id"
            class="platform-case-picker__row"
          >
            <span class="platform-case-picker__title">{{ row.title }}</span>
            <span class="platform-case-picker__steps">{{ row.stepCount }} 步</span>
          </el-checkbox>
        </el-checkbox-group>
      </template>
      <EmptyState
        v-else
        icon="📋"
        text="选一个用例表"
        hint="先选项目与用例表，这里列出可执行的用例；没有用例时请去用例管理导入 YAML"
      />
    </div>
  </div>
</template>

<style scoped>
.platform-case-picker {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  width: 100%;
}
.platform-case-picker__selects {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--app-space-sm);
}
.platform-case-picker__error {
  margin: 0;
  font-size: var(--app-size-xs);
  color: var(--app-status-danger-text);
}
.platform-case-picker__cases {
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  min-height: 96px;
  max-height: 220px;
  overflow-y: auto;
  padding: var(--app-space-sm);
}
.platform-case-picker__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-sm);
  padding-bottom: var(--app-space-xs);
  border-bottom: 1px solid color-mix(in srgb, var(--ink) 10%, transparent);
}
.platform-case-picker__count {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}
.platform-case-picker__list {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
  padding-top: var(--app-space-xs);
}
.platform-case-picker__row {
  display: flex;
  width: 100%;
}
.platform-case-picker__title {
  margin-right: var(--app-space-xs);
}
.platform-case-picker__steps {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}
</style>
