<script setup lang="ts">
/**
 * 平台用例选择器：项目栏 + 搜索 + 按项目分组的复选列表。
 *
 * 只做渲染与事件：过滤、分组、计数、提示文案与摘要全部走 `helpers/case-picker.ts`。
 * 已选由父级持有（v-model），**切项目不清空**；只有父级切「用例来源」或这里点「清空」才清。
 * 数据一次性来自 `GET /cases/projects/automation/`，本组件不发请求。
 */
import { computed, ref } from "vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import {
  countHitCases,
  filterCaseProjects,
  hitbarText,
  pickableIds,
  toggleAll,
  type CaseProjectGroup,
} from "../helpers/case-picker"

const props = defineProps<{
  /** 全部自动化项目及其用例 */
  projects: CaseProjectGroup[]
  /** 已选用例编号 */
  modelValue: string[]
  loading: boolean
  error: string
}>()

const emit = defineEmits<{
  "update:modelValue": [value: string[]]
  "retry": []
}>()

/** 当前项目范围：`all` 或某个项目编号。 */
const scope = ref<"all" | number>("all")
const query = ref("")

const totalCases = computed(() =>
  props.projects.reduce((total, project) => total + project.rows.length, 0),
)
const scopedProjects = computed(() =>
  scope.value === "all"
    ? props.projects
    : props.projects.filter((project) => project.id === scope.value),
)
const visibleGroups = computed(() => filterCaseProjects(scopedProjects.value, query.value))
const allHitGroups = computed(() => filterCaseProjects(props.projects, query.value))
const inScopeCount = computed(() => countHitCases(visibleGroups.value))
const elsewhereCount = computed(() => countHitCases(allHitGroups.value) - inScopeCount.value)
const scopeName = computed(
  () => props.projects.find((project) => project.id === scope.value)?.name || "全部项目",
)
const hitbar = computed(() => {
  if (!query.value.trim() || scope.value === "all") return ""
  return hitbarText({
    inScope: inScopeCount.value,
    elsewhere: elsewhereCount.value,
    projectName: scopeName.value,
  })
})

/** 项目栏：全部项目用总条数（搜索时用总命中数），各项目用自身条数。 */
const railItems = computed(() => {
  const keyword = query.value.trim()
  const allCount = keyword ? countHitCases(allHitGroups.value) : totalCases.value
  return [
    { key: "all" as const, name: "全部项目", count: allCount, disabled: false },
    ...props.projects.map((project) => {
      const count = keyword
        ? filterCaseProjects([project], keyword)[0]?.rows.length || 0
        : project.rows.length
      return {
        key: project.id,
        name: project.name,
        count,
        disabled: keyword.length > 0 && count === 0,
      }
    }),
  ]
})

function isPicked(id: string): boolean {
  return props.modelValue.includes(id)
}

function toggle(id: string): void {
  emit(
    "update:modelValue",
    isPicked(id) ? props.modelValue.filter((item) => item !== id) : [...props.modelValue, id],
  )
}

function toggleGroup(group: CaseProjectGroup): void {
  emit("update:modelValue", toggleAll(props.modelValue, pickableIds([group])))
}

function selectVisible(): void {
  emit("update:modelValue", toggleAll(props.modelValue, pickableIds(visibleGroups.value)))
}

function clearPicked(): void {
  emit("update:modelValue", [])
}

function pickScope(): void {
  scope.value = "all"
}
</script>

<template>
  <section class="case-picker" aria-label="平台用例选择器">
    <header class="case-picker__head">
      <span class="case-picker__title">自动化用例</span>
      <span class="case-picker__total">共 {{ totalCases }} 条</span>
      <span class="case-picker__picked">已选 {{ modelValue.length }} 条</span>
    </header>

    <div class="case-picker__search">
      <span class="case-picker__search-icon" aria-hidden="true">⌕</span>
      <input
        v-model="query"
        type="search"
        class="case-picker__input"
        placeholder="搜索用例名或编号，如 H6810"
        aria-label="搜索用例"
      />
      <button
        v-if="query"
        type="button"
        class="case-picker__clear-search"
        aria-label="清空搜索"
        @click="query = ''"
      >
        ✕
      </button>
    </div>

    <p v-if="hitbar" class="case-picker__hit" role="status">
      <span>{{ hitbar }}</span>
      <button type="button" class="case-picker__link" @click="pickScope">在全部项目中查看</button>
    </p>

    <div class="case-picker__grid">
      <nav class="case-picker__rail" aria-label="按项目筛选">
        <button
          v-for="item in railItems"
          :key="item.key"
          type="button"
          class="case-picker__rail-row"
          :class="{ 'is-on': scope === item.key }"
          :disabled="item.disabled"
          @click="scope = item.key"
        >
          <span class="case-picker__rail-name">{{ item.name }}</span>
          <span class="case-picker__rail-count">{{ item.count }}</span>
        </button>
      </nav>

      <div class="case-picker__listwrap">
        <div class="case-picker__bar">
          <span class="case-picker__scope">{{ scopeName }}</span>
          <button type="button" class="case-picker__link" @click="selectVisible">
            全选当前列表
          </button>
          <button type="button" class="case-picker__link" @click="clearPicked">清空</button>
        </div>

        <div class="case-picker__list">
          <SkeletonCard v-if="loading" variant="list" :lines="3" />
          <ErrorState v-else-if="error" :message="error" @retry="emit('retry')" />
          <EmptyState
            v-else-if="!projects.length"
            icon="📁"
            text="还没有自动化项目"
            hint="先去用例管理建一个自动化项目并导入用例"
          />
          <EmptyState
            v-else-if="!visibleGroups.length"
            icon="🔍"
            :text="`没有匹配「${query.trim()}」的用例`"
            hint="换个关键词，或清空搜索"
          >
            <button type="button" class="case-picker__link" @click="query = ''">清空搜索</button>
          </EmptyState>

          <template v-else>
            <div v-for="group in visibleGroups" :key="group.id" class="case-picker__group">
              <div class="case-picker__group-head">
                <span class="case-picker__group-name">{{ group.name }}</span>
                <span class="case-picker__group-count">{{ group.rows.length }} 条</span>
                <button type="button" class="case-picker__link" @click="toggleGroup(group)">
                  全选本项目
                </button>
              </div>
              <label
                v-for="row in group.rows"
                :key="row.id"
                class="case-picker__row"
                :class="{ 'is-on': isPicked(row.id) }"
              >
                <input
                  type="checkbox"
                  :checked="isPicked(row.id)"
                  :aria-label="row.title"
                  @change="toggle(row.id)"
                />
                <span class="case-picker__row-title" :title="row.title">{{ row.title }}</span>
                <code class="case-picker__row-id">{{ row.id }}</code>
              </label>
            </div>
          </template>
        </div>
      </div>
    </div>
  </section>
</template>

<style src="./CasePicker.style.css" scoped></style>
