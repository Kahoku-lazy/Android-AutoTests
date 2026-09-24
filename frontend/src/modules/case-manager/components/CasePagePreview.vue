<script setup lang="ts">
/**
 * 用例只读预览（用例管理工作台右栏专用）。
 *
 * 定位：右栏是**概览位**，只回答「这个文件里有哪些用例」。因此固定五列
 * （用例 ID · 测试类型 · 业务类型 · 标题 · 时间），通过共享分页让全部用例都可浏览；
 * 只调 getFileSheet 读数据——不导入任何写函数（createDefinition / updateDefinition /
 * deleteDefinition），也不渲染行内编辑、类型标签下拉、新建行 / 删除行 / 保存按键。
 * 「模块 / 前置 / 步骤 / 预期结果 / 操作」等列与全部编辑能力只在文件详情页
 * （/cases/projects/:projectId/files/:fileId）提供，本组件给一个进入那里的入口。
 */
import { computed, onMounted, ref, watch } from "vue"
import AppTable from "@/shared/components/AppTable.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { formatApiError } from "@/shared/api-client"
import { usePagination } from "@/shared/composables/usePagination"
import { getFileSheet } from "../api"
import {
  BUSINESS_TYPE_OPTIONS,
  TEST_TYPE_OPTIONS,
  type CaseDefinition,
  type TreeFileNode,
} from "../types"

/** 只读预览列：五列，顺序即展示顺序（其余列只在文件详情页） */
const PREVIEW_COLUMNS = [
  { dataIndex: "id", width: 150, label: "用例 ID", showOverflowTooltip: false },
  { dataIndex: "test_type", width: 96, align: "center", label: "测试类型", showOverflowTooltip: false },
  {
    dataIndex: "business_type",
    width: 96,
    align: "center",
    label: "业务类型",
    showOverflowTooltip: false,
  },
  { dataIndex: "title", minWidth: 200, label: "标题", showOverflowTooltip: false },
  { dataIndex: "updated_at", width: 170, label: "时间", showOverflowTooltip: false },
]

const props = defineProps<{ file: TreeFileNode }>()

const emit = defineEmits<{ open: [fileId: number] }>()

const loading = ref(false)
const error = ref("")
const rows = ref<CaseDefinition[]>([])

const { currentPage, totalPages, pagedItems, goPage } = usePagination(rows, { pageSize: 10 })

function labelOf(
  options: ReadonlyArray<{ value: string; label: string }>,
  value: string,
): string {
  return options.find((option) => option.value === value)?.label || value || "—"
}

const testTypeLabel = (value: string) => labelOf(TEST_TYPE_OPTIONS, value)
const businessTypeLabel = (value: string) => labelOf(BUSINESS_TYPE_OPTIONS, value)

async function load() {
  loading.value = true
  error.value = ""
  try {
    const { data } = await getFileSheet(props.file.id)
    if (data.status && data.data) {
      rows.value = data.data.rows || []
    } else {
      error.value = data.message || "用例预览加载失败"
      rows.value = []
    }
  } catch (e: unknown) {
    error.value = formatApiError(e as never, "用例预览加载失败")
    rows.value = []
  } finally {
    loading.value = false
  }
}

const total = computed(() => rows.value.length)

watch(() => props.file.id, load)
onMounted(load)
</script>

<template>
  <section class="case-preview">
    <header class="case-preview__head">
      <div class="case-preview__title-block">
        <h3 class="case-preview__title">{{ file.name }}</h3>
        <span class="case-preview__meta">共 {{ total }} 条用例 · 只读预览</span>
      </div>
      <el-button type="primary" @click="emit('open', file.id)">进入页面编辑 ›</el-button>
    </header>

    <div class="case-preview__body">
      <SkeletonCard v-if="loading" variant="list" :lines="6" />
      <ErrorState v-else-if="error" :message="error" @retry="load" />

      <EmptyState
        v-else-if="!rows.length"
        icon="📋"
        text="该文件暂无用例"
        hint="进入页面后可用「新建行」开始填写"
      >
        <el-button type="primary" @click="emit('open', file.id)">进入页面编辑 ›</el-button>
      </EmptyState>

      <template v-else>
        <div class="case-preview__sheet">
          <AppTable
            :columns="PREVIEW_COLUMNS"
            :data-source="pagedItems"
            accent="var(--c-case)"
            border
            :striped="true"
            height="100%"
            class="case-preview-table"
            row-key="id"
            empty-text="暂无用例"
          >
            <template #cell-id="{ row }">
              <span class="case-preview__text" :title="row.id">{{ row.id }}</span>
            </template>
            <template #cell-test_type="{ row }">
              <span class="case-preview__tag">{{ testTypeLabel(row.test_type) }}</span>
            </template>
            <template #cell-business_type="{ row }">
              <span class="case-preview__tag">{{ businessTypeLabel(row.business_type) }}</span>
            </template>
            <template #cell-title="{ row }">
              <span class="case-preview__text" :title="row.title">{{ row.title || "—" }}</span>
            </template>
            <template #cell-updated_at="{ row }">
              <span class="case-preview__text">{{ row.updated_at || "—" }}</span>
            </template>
          </AppTable>
        </div>

        <footer class="case-preview__foot">
          <div class="case-preview__pager">
            <span>第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ total }} 条</span>
            <el-button size="small" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">
              上一页
            </el-button>
            <el-button
              size="small"
              :disabled="currentPage >= totalPages"
              @click="goPage(currentPage + 1)"
            >
              下一页
            </el-button>
          </div>
        </footer>
      </template>
    </div>
  </section>
</template>

<style scoped>
/* 只读预览：概览位。五列，其余列与编辑能力都在文件详情页 */
.case-preview {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: var(--app-space-md) var(--app-space-lg) var(--app-space-lg);
  gap: var(--app-space-md);
}
.case-preview__head {
  display: flex;
  align-items: center;
  gap: var(--app-space-md);
  flex-wrap: wrap;
  flex-shrink: 0;
}
.case-preview__title-block {
  min-width: 0;
  flex: 1 1 auto;
}
.case-preview__title {
  font-size: var(--app-size-lg);
  font-weight: 800;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.case-preview__meta {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  font-weight: 700;
}
.case-preview__body {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
}
.case-preview__sheet {
  flex: 1 1 0;
  min-height: 0;
}
.case-preview-table {
  height: 100%;
}
.case-preview__foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--app-space-md);
  flex-wrap: wrap;
  flex-shrink: 0;
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
}
.case-preview__pager {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
}
.case-preview__text {
  color: var(--ink);
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}
.case-preview__tag {
  display: inline-block;
  border: 1px solid var(--ink);
  border-radius: 2px;
  padding: 0 var(--app-space-xs);
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--ink);
  background: var(--app-bg-input);
}
</style>
